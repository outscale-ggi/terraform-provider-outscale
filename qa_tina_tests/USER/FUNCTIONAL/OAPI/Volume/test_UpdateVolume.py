import uuid

import pytest

from qa_common_tools.ssh import SshTools
from qa_test_tools.test_base import OscTestSuite

from qa_test_tools.config import config_constants as constants
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming import write_on_device
from qa_tina_tools.tina.check_tools import format_mount_volume, create_text_file_volume, read_text_file_volume, \
    umount_volume
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, INSTANCE_SET, PATH, KEY_PAIR
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state, wait_volumes_state

class Test_UpdateVolume(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateVolume, cls).setup_class()
        cls.ret_link = None
        cls.vol_id = None
        cls.sshclient = None
        cls.with_md5sum = True
        cls.with_fio = True
        cls.inst_info = None
        cls.device = None
        cls.volume_mount = None
        cls.is_attached = False

    @classmethod
    def teardown_class(cls):
        super(Test_UpdateVolume, cls).teardown_class()

    def setup_method(self, method):
        super(Test_UpdateVolume, self).setup_method(method)
        try:
            vm_type = self.a1_r1.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE)
            self.inst_info = create_instances(self.a1_r1, state='running', inst_type=vm_type)
            self.vol_id = self.a1_r1.oapi.CreateVolume(VolumeType='standard', Size=2,
                                                       SubregionName=self.azs[0]).response.Volume.VolumeId
            wait_volumes_state(self.a1_r1, [self.vol_id], state='available')
            self.ret_link = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id, VmId=self.inst_info[INSTANCE_ID_LIST][0],
                                                       DeviceName='/dev/xvdc')
            wait_volumes_state(self.a1_r1, [self.vol_id], state='in-use')
            self.is_attached = True

            wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=self.inst_info[INSTANCE_ID_LIST], state='ready')

            self.sshclient = SshTools.check_connection_paramiko(self.inst_info[INSTANCE_SET][0]['ipAddress'],
                                                                self.inst_info[KEY_PAIR][PATH],
                                                                username=self.a1_r1.config.region.get_info(
                                                                    constants.CENTOS_USER))
            if self.with_fio:
                cmd = 'sudo yum install -y epel-release'
                SshTools.exec_command_paramiko_2(self.sshclient, cmd)
                cmd = 'sudo yum install -y fio'
                SshTools.exec_command_paramiko_2(self.sshclient, cmd)

            self.device = '/dev/xvdc'
            self.volume_mount = '/mnt/vol'
            format_mount_volume(self.sshclient, self.device, self.volume_mount, True)
        except:
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.is_attached:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id)
                wait_volumes_state(self.a1_r1, [self.vol_id], state='available')
            if self.vol_id:
                self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol_id)
            if self.inst_info:
                delete_instances(self.a1_r1, self.inst_info)
        except Exception as error:
            self.logger.exception(error)
            pytest.fail("An unexpected error happened : " + str(error))

    def test_check_data_before(self):
        try:
            test_file = "test_volumes.txt"
            text_to_check = uuid.uuid4().hex
            create_text_file_volume(self.sshclient, self.volume_mount, test_file, text_to_check)
            umount_volume(self.sshclient, self.volume_mount)

            self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id)
            wait_volumes_state(self.a1_r1, [self.vol_id], state='available')
            self.is_attached = False

            #resp = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_id, Size=5).response
            #wait_volumes_state(self.a1_r1, [self.vol_id], state='available')

            self.ret_link = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id, VmId=self.inst_info[INSTANCE_ID_LIST][0],
                                                       DeviceName='/dev/xvdc')
            wait_volumes_state(self.a1_r1, [self.vol_id], state='in-use')
            self.is_attached = True

            cmd = 'sudo mount -o nouuid {} {}'.format(self.device, self.volume_mount)
            SshTools.exec_command_paramiko_2(self.sshclient, cmd)

            read_text_file_volume(self.sshclient, self.volume_mount, test_file, text_to_check)

        except Exception as error:
            self.logger.exception(error)
            pytest.fail("An unexpected error happened : " + str(error))

    def test_real_volume_size(self):
        # resp = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_id, Size=5).response
        wait_volumes_state(self.a1_r1, [self.vol_id], state='available')
        self.ret_link = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id, VmId=self.inst_info[INSTANCE_ID_LIST][0],
                                                   DeviceName='/dev/xvdc')
        wait_volumes_state(self.a1_r1, [self.vol_id], state='in-use')
        md5sum = write_on_device(sshclient=self.sshclient, device=self.device, folder=self.volume_mount, f_num=1,
                                 size=10**3, with_md5sum=self.with_md5sum, with_fio=self.with_fio)
        assert md5sum
