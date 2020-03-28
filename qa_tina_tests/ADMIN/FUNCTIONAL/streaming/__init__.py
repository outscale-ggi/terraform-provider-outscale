# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import time
import re
import pytest

from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_volumes
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state, wait_volumes_state, wait_instances_state
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, INSTANCE_SET, KEY_PAIR, PATH
from qa_common_tools.misc import assert_error
from qa_common_tools.config import config_constants as constants
from qa_common_tools.ssh import SshTools
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.utils import write_on_device, read_on_device, assert_streaming_state, wait_streaming_state, get_streaming_operation,\
    get_data_file_chain


class StreamingBase(OscTestSuite):

    w_size = None
    v_size = None
    qemu_version = None
    inst_type = None
    vol_type = None
    iops = None
    s_len = None
    branch = None
    with_md5sum = None
    with_fio = None

    @classmethod
    def setup_class(cls):
        """
            Init
            snap_0 --- snap_1 --- snap_2 --- snap_3 --- snap_4 --- snap_... --- snap_n--- vol
                          |          |          |
                          |          |           `--- snap_30 --- snap_31
                          |           `--- snap_20 --- snap_21
                           `--- snap_10 --- snap_11
        """
        cls.cleanup = True
        # cls.w_size = 1 # size of written files
        # cls.v_size = 10 # size of volume
        # cls.qemu_version = '2.12' # QEMU version used for the test
        # cls.inst_type = 'm4.large' # instance type
        # cls.vol_type = 'standard' # volume type
        # cls.iops = 100
        # cls.s_len = 5 # number of created snapshot (len of datafiles chain)
        # cls.branch = True # Define if new sub-branch created in datafiles chain
        # cls.with_md5sum = True
        # cls.with_fio = False
        cls.sshclient = None
        cls.test_sshclient = None
        cls.inst_info = None
        cls.tmp_inst_info = None
        cls.vol_id = None
        cls.vol_attached = False
        cls.data = {}
        cls.data_test = {}
        cls.vol_id_test = None
        cls.data_file_before = []
        super(StreamingBase, cls).setup_class()
        try:
            if cls.qemu_version == '2.12':
                cls.inst_info = create_instances(cls.a1_r1, state='running', inst_type=cls.inst_type)
                cls.test_inst_info = create_instances(cls.a1_r1, state='running', inst_type=cls.inst_type)
            else:
                cls.inst_info = create_instances(cls.a1_r1, state='running', inst_type=cls.inst_type, dedicated=True)
                cls.test_inst_info = create_instances(cls.a1_r1, state='running', inst_type=cls.inst_type, dedicated=True)
            _, vol_id_list = create_volumes(cls.a1_r1, size=cls.v_size, volume_type=cls.vol_type, iops=cls.iops)
            cls.vol_id = vol_id_list[0]
            wait_volumes_state(cls.a1_r1, [cls.vol_id], 'available', nb_check=5)
            cls.a1_r1.intel.volume.update(owner=cls.a1_r1.config.account.account_id, volume=cls.vol_id, streamable=False)
            cls.a1_r1.fcu.AttachVolume(InstanceId=cls.inst_info[INSTANCE_ID_LIST][0], VolumeId=cls.vol_id, Device='/dev/xvdb')
            wait_volumes_state(cls.a1_r1, [cls.vol_id], state='in-use', nb_check=5)
            cls.vol_attached = True

            wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=cls.inst_info[INSTANCE_ID_LIST], state='ready')

            # init ssh
            cls.sshclient = SshTools.check_connection_paramiko(cls.inst_info[INSTANCE_SET][0]['ipAddress'], cls.inst_info[KEY_PAIR][PATH],
                                                               username=cls.a1_r1.config.region.get_info(constants.CENTOS_USER))
            if cls.with_fio:
                cmd = 'sudo yum install -y epel-release'
                SshTools.exec_command_paramiko_2(cls.sshclient, cmd)
                cmd = 'sudo yum install -y fio'
                SshTools.exec_command_paramiko_2(cls.sshclient, cmd)

            # format volume
            cmd = 'sudo mkfs.xfs -f /dev/xvdb'
            SshTools.exec_command_paramiko_2(cls.sshclient, cmd, eof_time_out=120)

            # loop
            for i in range(cls.s_len):
                # mount / write / umount
                md5sum = write_on_device(sshclient=cls.sshclient, device='/dev/xvdb', folder='/mnt', f_num=i, size=cls.w_size,
                                         with_md5sum=cls.with_md5sum, with_fio=cls.with_fio)
                # snap
                snap_id = cls.a1_r1.fcu.CreateSnapshot(VolumeId=cls.vol_id).response.snapshotId
                wait_snapshots_state(osc_sdk=cls.a1_r1, state='completed', snapshot_id_list=[snap_id])
                ret = cls.a1_r1.intel.snapshot.find(id=snap_id)
                ret = cls.a1_r1.intel.storage.get_data_file_chain(file_id=ret.response.result[0].data_file)
                datafiles = [i.id for i in ret.response.result]
                cls.data['snap_{}'.format(i)] = {'id': snap_id, 'md5sum': md5sum, 'datafiles': datafiles}
                if cls.branch and i > 0 and i < 4:
                    _, vol_id_list = create_volumes(cls.a1_r1, snapshot_id=snap_id, size=cls.v_size, volume_type=cls.vol_type, iops=cls.iops)
                    vol_id = vol_id_list[0]
                    wait_volumes_state(cls.a1_r1, [vol_id], 'available', nb_check=5)
                    cls.a1_r1.fcu.AttachVolume(InstanceId=cls.inst_info[INSTANCE_ID_LIST][0], VolumeId=vol_id, Device='/dev/xvdc')
                    wait_volumes_state(cls.a1_r1, [vol_id], state='in-use', nb_check=5)

                    for j in range(1):
                        md5sum = write_on_device(sshclient=cls.sshclient, device='/dev/xvdc', folder='/mnt', f_num=i * 100 + j, size=cls.w_size,
                                                 with_md5sum=cls.with_md5sum, with_fio=cls.with_fio)
                        snap_id = cls.a1_r1.fcu.CreateSnapshot(VolumeId=vol_id).response.snapshotId
                        wait_snapshots_state(osc_sdk=cls.a1_r1, state='completed', snapshot_id_list=[snap_id])
                        ret = cls.a1_r1.intel.snapshot.find(id=snap_id)
                        ret = cls.a1_r1.intel.storage.get_data_file_chain(file_id=ret.response.result[0].data_file)
                        datafiles = [i.id for i in ret.response.result]
                        cls.data['snap_{}'.format(i * 100 + j)] = {'id': snap_id, 'md5sum': md5sum, 'datafiles': datafiles}
                    cls.a1_r1.fcu.DetachVolume(VolumeId=vol_id)
                    wait_volumes_state(cls.a1_r1, [vol_id], 'available', nb_check=5)
                    delete_volumes(cls.a1_r1, [vol_id])

            wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=cls.test_inst_info[INSTANCE_ID_LIST], state='ready')
            cls.test_sshclient = SshTools.check_connection_paramiko(cls.test_inst_info[INSTANCE_SET][0]['ipAddress'],
                                                                    cls.test_inst_info[KEY_PAIR][PATH],
                                                                    username=cls.a1_r1.config.region.get_info(constants.CENTOS_USER))
            if cls.with_fio:
                cmd = 'sudo yum install -y epel-release'
                SshTools.exec_command_paramiko_2(cls.test_sshclient, cmd)
                cmd = 'sudo yum install -y fio'
                SshTools.exec_command_paramiko_2(cls.test_sshclient, cmd)

            cls.a1_r1.fcu.DetachVolume(VolumeId=cls.vol_id)
            wait_volumes_state(cls.a1_r1, [cls.vol_id], 'available', nb_check=5)
            cls.vol_attached = False

        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.cleanup:
                for _, value in list(cls.data.items()):
                    cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=value['id'])
                    wait_snapshots_state(osc_sdk=cls.a1_r1, cleanup=True, snapshot_id_list=[value['id']])
                if cls.vol_attached:
                    wait_volumes_state(cls.a1_r1, [cls.vol_id], 'in-use', nb_check=5)
                    cls.a1_r1.fcu.DetachVolume(VolumeId=cls.vol_id)
                    try:
                        wait_volumes_state(cls.a1_r1, [cls.vol_id], 'available', nb_check=5)
                    except AssertionError:
                        cls.logger.debug("Retry detach...")
                        cls.a1_r1.fcu.DetachVolume(VolumeId=cls.vol_id)
                        wait_volumes_state(cls.a1_r1, [cls.vol_id], 'available', nb_check=5)
                if cls.vol_id:
                    delete_volumes(cls.a1_r1, [cls.vol_id])
                if cls.test_inst_info:
                    delete_instances(cls.a1_r1, cls.test_inst_info)
                if cls.inst_info:
                    delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(StreamingBase, cls).teardown_class()

    def setup_method(self, method):
        """
            Init
            snap_0 --- snap_1 --- snap_2 --- snap_3 --- snap_4 --- snap_... --- snap_n --- vol
                          |          |          |                                  `--- snap_n+1 --- vol_test
                          |          |           `--- snap_30 --- snap_31
                          |           `--- snap_20 --- snap_21
                           `--- snap_10 --- snap_11
        """
        super(StreamingBase, self).setup_method(method)
        self.data_test = {}
        self.vol_id_test = None
        self.data_file_before = []
        try:
            _, vol_id_list = create_volumes(self.a1_r1, snapshot_id=self.data['snap_{}'.format(self.s_len - 1)]['id'], size=self.v_size,
                                            volume_type=self.vol_type, iops=self.iops)
            self.vol_id_test = vol_id_list[0]
            wait_volumes_state(self.a1_r1, [self.vol_id_test], 'available', nb_check=5)
            self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], VolumeId=self.vol_id_test, Device='/dev/xvdc')
            wait_volumes_state(self.a1_r1, [self.vol_id_test], state='in-use', nb_check=5)
            md5sum = write_on_device(sshclient=self.sshclient, device='/dev/xvdc', folder='/mnt', f_num=self.s_len, size=self.w_size,
                                     with_md5sum=self.with_md5sum, with_fio=self.with_fio)
            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id_test).response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap_id])
            datafiles = get_data_file_chain(self.a1_r1, res_id=snap_id)
            self.data_test['snap_{}'.format(self.s_len)] = {'id': snap_id, 'md5sum': md5sum, 'datafiles': datafiles}

            self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_id_test)
            wait_volumes_state(self.a1_r1, [self.vol_id_test], 'available', nb_check=5)
            self.a1_r1.fcu.AttachVolume(InstanceId=self.test_inst_info[INSTANCE_ID_LIST][0], VolumeId=self.vol_id_test, Device='/dev/xvdb')
            wait_volumes_state(self.a1_r1, [self.vol_id_test], state='in-use', nb_check=5)

            ret = wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=self.test_inst_info[INSTANCE_ID_LIST], state='ready')
            self.test_sshclient = SshTools.check_connection_paramiko(ret.response.reservationSet[0].instancesSet[0].ipAddress,
                                                                     self.test_inst_info[KEY_PAIR][PATH],
                                                                     username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            cmd = 'sudo mkdir -p /vol; sudo mount -o nouuid /dev/xvdb /vol'
            SshTools.exec_command_paramiko_2(self.test_sshclient, cmd)

            self.data_file_before = get_data_file_chain(self.a1_r1, res_id=self.vol_id_test)
            assert len(self.data_file_before) > 1

        except:
            try:
                out, status, err = SshTools.exec_command_paramiko_2(self.test_sshclient, "sudo dmesg")
                self.logger.debug(out)
                self.logger.debug(status)
                self.logger.debug(err)
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            out, status, err = SshTools.exec_command_paramiko_2(self.test_sshclient, "sudo dmesg")
            self.logger.debug(out)
            self.logger.debug(status)
            self.logger.debug(err)
            if self.cleanup:
                cmd = 'sudo umount /vol'
                SshTools.exec_command_paramiko_2(self.test_sshclient, cmd)
                if self.vol_id_test:
                    wait_volumes_state(self.a1_r1, [self.vol_id_test], 'in-use', nb_check=5)
                    self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_id_test)
                    try:
                        wait_volumes_state(self.a1_r1, [self.vol_id_test], 'available', nb_check=5)
                    except AssertionError:
                        self.logger.debug("Retry detach...")
                        self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_id_test)
                        wait_volumes_state(self.a1_r1, [self.vol_id_test], 'available', nb_check=5)
                    delete_volumes(self.a1_r1, [self.vol_id_test])
                for _, value in list(self.data_test.items()):
                    self.a1_r1.fcu.DeleteSnapshot(SnapshotId=value['id'])
                    wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=[value['id']])
        finally:
            super(StreamingBase, self).teardown_method(method)

    def get_data_file_chain(self, res_id):
        if res_id.startswith('vol-'):
            ret = self.a1_r1.intel.volume.find(id=res_id)
        elif res_id.startswith('snap-'):
            ret = self.a1_r1.intel.snapshot.find(id=res_id)
        ret = self.a1_r1.intel.storage.get_data_file_chain(file_id=ret.response.result[0].data_file)
        return [i.id for i in ret.response.result]

    def check_data(self):
        """
            create new volumes from each snapshot and check md5sum with previously saved md5sum
        """
        for _, value in list(self.data.items()):
            data_file_after = self.get_data_file_chain(res_id=value['id'])
            assert data_file_after == value['datafiles']

            vol_id = None
            ret_attach = None
            _, [vol_id] = create_volumes(self.a1_r1, snapshot_id=value['id'], size=self.v_size, volume_type=self.vol_type, iops=self.iops)
            try:
                wait_volumes_state(self.a1_r1, [vol_id], 'available', nb_check=5)
                ret_attach = self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], VolumeId=vol_id, Device='/dev/xvdc')
                wait_volumes_state(self.a1_r1, [vol_id], state='in-use', nb_check=5)
                md5sum = read_on_device(sshclient=self.sshclient, device='/dev/xvdc', folder='/mnt', with_md5sum=self.with_md5sum)
            finally:
                if ret_attach:
                    self.a1_r1.fcu.DetachVolume(VolumeId=vol_id)
                    wait_volumes_state(self.a1_r1, [vol_id], 'available', nb_check=5)
                if vol_id:
                    delete_volumes(self.a1_r1, [vol_id])
            assert md5sum == value['md5sum']

    def check_full_streaming(self):
        data_file_after = get_data_file_chain(self.a1_r1, res_id=self.vol_id_test)
        # check data file chain
        if self.qemu_version == '2.3':
            assert len(data_file_after) == 1
            assert data_file_after[0] == self.data_file_before[0]
        else:
            assert len(data_file_after) == 3
            assert data_file_after[0] == self.data_file_before[0]
            assert data_file_after[1] == self.data_file_before[1]
            assert data_file_after[2] == self.data_file_before[-1]

    def check_intermediate_streaming(self):
        data_file_after = get_data_file_chain(self.a1_r1, res_id=self.vol_id_test)
        # check data file chain
        if self.qemu_version == '2.3':
            # ???
            assert len(data_file_after) == 1
            assert data_file_after[0] == self.data_file_before[0]
        else:
            assert len(data_file_after) == 6
            assert data_file_after[0] == self.data_file_before[0]
            assert data_file_after[1] == self.data_file_before[1]
            assert data_file_after[2] == self.data['snap_2']['datafiles'][0]
            assert data_file_after[3] == self.data['snap_2']['datafiles'][1]
            assert data_file_after[4] == self.data['snap_2']['datafiles'][2]
            assert data_file_after[5] == self.data['snap_2']['datafiles'][3]

