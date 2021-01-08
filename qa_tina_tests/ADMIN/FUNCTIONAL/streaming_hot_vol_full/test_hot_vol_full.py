# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import pytest

from qa_common_tools.ssh import SshTools
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import assert_error
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.utils import wait_streaming_state, assert_streaming_state, get_data_file_chain, write_data
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming_hot.base import StreamingBaseHot
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_volumes
from qa_tina_tools.tools.tina.info_keys import KEY_PAIR, PATH, INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state, wait_volumes_state, wait_instances_state


@pytest.mark.region_admin
@pytest.mark.tag_qemu
class Test_hot_vol_full(StreamingBaseHot):

    @classmethod
    def setup_class(cls):
        cls.w_size = 20
        cls.v_size = 10
        cls.qemu_version = '2.12'
        #cls.rebase_enabled = False
        cls.inst_type = 'c4.xlarge'
        cls.vol_type = 'standard'
        cls.iops = None
        cls.base_snap_id = 10
        cls.new_snap_count = 1  # > 1
        cls.branch_id = None  # [0, new_snap_count-1]
        cls.fio = False
        cls.inst_running = True
        cls.inst_stopped = False
        cls.check_data = True
        super(Test_hot_vol_full, cls).setup_class()

    def test_T3126_hot_vol_full(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
        wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
        self.check_stream_full()

    def test_T4135_hot_vol_full_not_streamable(self):
        self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=False)
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-state - Volume is not allowed to stream (attr: streamable)')
        finally:
            self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=True)

    def test_T3301_hot_vol_full_and_detach(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        self.detach(resource_id=self.vol_1_id)
        if self.rebase_enabled:
            self.check_stream_full()
        else:
            self.check_no_stream()

    def test_T3302_hot_vol_full_and_stop(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        self.stop(resource_id=self.vol_1_id)
        self.check_stream_full()

    def test_T3300_hot_vol_full_and_snapshot(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        self.snapshot(resource_id=self.vol_1_id)
        self.check_stream_full(nb_new_snap=1)

    def test_T3303_hot_vol_full_and_reboot(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        self.reboot(resource_id=self.vol_1_id)
        self.check_stream_full()

    def test_T3381_hot_vol_full_and_delete_snap(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        self.delete_snap(resource_id=self.vol_1_id, snap_id=self.vol_1_snap_list[-1])
        self.check_stream_full()
        #self.vol_1_snap_list.remove(self.vol_1_snap_list[-1])

    def test_T3305_hot_vol_full_and_stream_twice(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
            assert False
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-state - Streaming already started')
        assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
        wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
        self.check_stream_full()

    def test_T4361_hot_vol_full_without_snapshots_on_last_datafiles(self):
        ret = wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=self.inst_running_info[INSTANCE_ID_LIST], state='ready')
        sshclient = SshTools.check_connection_paramiko(ret.response.reservationSet[0].instancesSet[0].ipAddress, self.inst_running_info[KEY_PAIR][PATH],
                                                       username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        for i in range(5):
            write_data(sshclient=sshclient, f_num=100+i, device='/dev/xvdc', folder='/mnt', w_size=self.w_size, fio=False)
            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_1_id, Description='S{}'.format(100+i)).response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap_id])
            self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=[snap_id])
        cmd = 'sudo mount -o nouuid {} {}'.format('/dev/xvdc', '/mnt')
        SshTools.exec_command_paramiko(sshclient, cmd)
        cmd = 'sudo cat {}/data_*.txt | md5sum'.format('/mnt')
        out, _, _ = SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=300)
        self.md5sum_before = out.split(' ')[0]
        cmd = 'sudo umount {}'.format('/mnt')
        SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=300)

        data_file_before = get_data_file_chain(self.a1_r1, res_id=self.vol_1_id)

        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
        wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)

        data_file_after = get_data_file_chain(self.a1_r1, res_id=self.vol_1_id)
        assert len(data_file_after) == 2
        assert data_file_after[0] == data_file_before[0]
        assert data_file_after[1] == data_file_before[1]

    def test_T4446_hot_vol_full_and_attach_other_vol(self):
        vol_2_id = None
        attached = False
        try:
            # create vol2
            _, [vol_2_id] = create_volumes(self.a1_r1, snapshot_id=self.vol_1_snap_list[-1], size=self.v_size, volume_type=self.vol_type,
                                           iops=self.iops)
            wait_volumes_state(self.a1_r1, [vol_2_id], 'available')
            # start streaming
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
            assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
            # attach vol2
            self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_running_info[INSTANCE_ID_LIST][0], VolumeId=vol_2_id, Device='/dev/xvdz')
            attached = True
            # check streaming task
            wait_streaming_state(self.a1_r1, self.vol_1_id, state='interrupted', logger=self.logger)
            # check vol2 attachement
            wait_volumes_state(self.a1_r1, [vol_2_id], state='in-use')
            # check vol1 DF
            self.check_no_stream()
        finally:
            if attached:
                self.a1_r1.fcu.DetachVolume(VolumeId=vol_2_id)
                try:
                    wait_volumes_state(self.a1_r1, [vol_2_id], state='available')
                except AssertionError:
                    self.logger.debug("Retry detach...")
                    self.a1_r1.fcu.DetachVolume(VolumeId=vol_2_id)
                    wait_volumes_state(self.a1_r1, [vol_2_id], 'available')
            if vol_2_id:
                # delete vol2
                delete_volumes(self.a1_r1, [vol_2_id])

    #def test_T3306_hot_vol_full_and_stream_diff_df_chain_on_same_instance(self):
    #    vol_id = None
    #    snap_id_list = []
    #    attached = False
    #    try:
    #        # init new chain
    #        _, vol_id = create_volumes(self.a1_r1, snapshot_id=self.data_test['snap_{}'.format(self.s_len)]['id'], size=self.v_size,
    #                                   volume_type=self.vol_type, iops=self.iops)
    #        vol_id = vol_id[0]
    #        wait_volumes_state(self.a1_r1, [vol_id], 'available', nb_check=5)
    #        # attach and mount
    #        self.a1_r1.fcu.AttachVolume(InstanceId=self.test_inst_info[INSTANCE_ID_LIST][0], VolumeId=vol_id, Device='/dev/xvdd')
    #        wait_volumes_state(self.a1_r1, [vol_id], state='in-use', nb_check=5)
    #        attached = True
    #        cmd = 'sudo mkfs.xfs -f /dev/xvdd; sudo mkdir -p /vol2; sudo mount /dev/xvdd /vol2'
    #        SshTools.exec_command_paramiko(self.test_sshclient, cmd)
    #        for _ in range(self.s_len):
    #            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=vol_id).response.snapshotId
    #            wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap_id])
    #            snap_id_list.append(snap_id)
    #        # start streaming
    #        self.a1_r1.intel.streaming.start(resource_id=self.vol_id_test)
    #        assert_streaming_state(self.a1_r1, self.vol_id_test, 'started', self.logger)

    #        # try to stream new chain
    #        try:
    #            self.a1_r1.intel.streaming.start(resource_id=vol_id)
    #            assert False
    #        except OscApiException as error:
    #            assert_error(error, 200, 0, 'invalid-vm-state - Another resource is being streamed')

    #        assert_streaming_state(self.a1_r1, self.vol_id_test, 'started', self.logger)
    #        wait_streaming_state(self.a1_r1, self.vol_id_test, cleanup=True, logger=self.logger)
    #        self.check_full_streaming()

    #    finally:
    #        if attached:
    #            # umount and detach
    #            cmd = 'sudo umount /vol2'
    #            SshTools.exec_command_paramiko(self.test_sshclient, cmd)
    #            self.a1_r1.fcu.DetachVolume(VolumeId=vol_id)
    #            wait_volumes_state(self.a1_r1, [vol_id], 'available', nb_check=5)
    #        # clean new chain
    #        for snap_id in snap_id_list:
    #            self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
    #            wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=[snap_id])
    #        if vol_id:
    #            delete_volumes(self.a1_r1, [vol_id])
