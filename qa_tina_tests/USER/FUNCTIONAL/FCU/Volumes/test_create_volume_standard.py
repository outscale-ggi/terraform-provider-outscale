import uuid

import pytest

from qa_test_tools.config import config_constants as constants
from qa_tina_tools.tina import check_tools
from qa_tina_tools.tina.check_tools import check_volume
from qa_tina_tools.tina.info_keys import PATH
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state
from qa_tina_tests.USER.FUNCTIONAL.FCU.Volumes.create_volume import CreateVolume


class Test_create_volume_standard(CreateVolume):
    """
        check that from a set of regions
        the others set regions are not available
    """

    @classmethod
    def setup_class(cls):
        super(Test_create_volume_standard, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_create_volume_standard, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T55_create_volume_std(self):
        self.create_volume(volume_type='standard', volume_size=1)

    def test_T3157_check_iops_volume_standard(self):
        self.create_volume(volume_type='standard', volume_size=100, perf_iops=20, drive_letter_code='c')

    def test_T3025_attach_detach_attach_volume_std(self):
        try:
            dev = '/dev/xvdb'
            text_to_check = uuid.uuid4().hex
            _, vol_id_list = create_volumes(self.a1_r1, volume_type='standard', size=8, state='available', iops=None)
            self.volume_id = vol_id_list[0]
            self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_id, VolumeId=self.volume_id, Device=dev)
            wait_volumes_state(self.a1_r1, [self.volume_id], state='in-use', cleanup=False, threshold=20, wait_time=3)
            check_volume(self.sshclient, dev, 8, text_to_check=text_to_check)
            self.a1_r1.fcu.DetachVolume(InstanceId=self.inst_id, VolumeId=self.volume_id)
            wait_volumes_state(self.a1_r1, [self.volume_id], 'available')
            self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_id, VolumeId=self.volume_id, Device=dev)
            wait_volumes_state(self.a1_r1, [self.volume_id], state='in-use', cleanup=False, threshold=20, wait_time=3)
            self.sshclient = check_tools.check_ssh_connection(self.a1_r1, self.inst_id, self.public_ip_inst, self.kp_info[PATH],
                                                              username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # self.sshclient = SshTools.check_connection_paramiko(self.public_ip_inst, self.kp_info[PATH],
            # username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            check_volume(self.sshclient, dev, 8, with_format=False, text_to_check=text_to_check, no_create=True)
        finally:
            try:
                if self.volume_id:
                    self.a1_r1.fcu.DetachVolume(VolumeId=self.volume_id)
                    wait_volumes_state(self.a1_r1, [self.volume_id], state='available', cleanup=False, threshold=20, wait_time=3)
                self.a1_r1.fcu.DeleteVolume(VolumeId=self.volume_id)
            except Exception as error:
                pytest.fail("An unexpected error happened while cleaning: " + str(error))
