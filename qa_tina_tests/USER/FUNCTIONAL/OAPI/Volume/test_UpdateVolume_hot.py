import uuid

from qa_sdk_common.exceptions import OscApiException
from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import oapi, wait, info_keys
from qa_tina_tools.tina.check_tools import check_volume
from qa_tina_tools.tina.wait import wait_Volumes_state


class Test_UpdateVolume_Hot(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateVolume_Hot, cls).setup_class()
        cls.vm_info = None
        cls.text_to_check = None
        cls.initial_size = 10
        cls.dev = '/dev/xvdc'
        cls.vol_id = None
        cls.linked = None
        cls.sshclient = None
        cls.initial_iops = 200
        try:
            cls.vm_info = oapi.create_Vms(cls.a1_r1, state='running')

        except Exception as error:
            try:
                cls.teardown_class()
            except Exception as err:
                raise err
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vm_info:
                oapi.delete_Vms(cls.a1_r1, cls.vm_info)
        finally:
            super(Test_UpdateVolume_Hot, cls).teardown_class()

    def setup_method(self, method):
        super(Test_UpdateVolume_Hot, self).setup_method(method)
        self.vol_id = None
        self.linked = None
        self.sshclient = None
        self.text_to_check = None
        try:
            kp_path = self.vm_info[info_keys.KEY_PAIR][info_keys.PATH]
            az_name = self.a1_r1.config.region.az_name
            initial_size = 10
            self.vol_id = self.a1_r1.oapi.CreateVolume(VolumeType='io1', Size=initial_size, Iops=self.initial_iops,
                                                       SubregionName=az_name).response.Volume.VolumeId
            wait_Volumes_state(self.a1_r1, [self.vol_id], 'available')
            self.linked = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id, VmId=self.vm_info[info_keys.VM_IDS][0], DeviceName=self.dev)
            wait_Volumes_state(self.a1_r1, [self.vol_id], 'in-use')

            wait.wait_Vms_state(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], state='ready')
            self.sshclient = SshTools.check_connection_paramiko(self.vm_info[info_keys.VMS][0]['PublicIp'], kp_path,
                                                                username=self.a1_r1.config.region.get_info(
                                                               constants.CENTOS_USER))

            self.text_to_check = uuid.uuid4().hex
            check_volume(self.sshclient, dev=self.dev, size=initial_size, text_to_check=self.text_to_check, volume_type='io1',
                         iops_io1=self.initial_iops)

        except Exception as error:
            try:
                self.teardown_method(method)
            except Exception as err:
                raise err
            finally:
                raise error

    def teardown_method(self, method):
        try:
            if self.linked:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id)
                wait_Volumes_state(self.a1_r1, [self.vol_id], 'available')
            if self.vol_id:
                self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol_id)
        finally:
            super(Test_UpdateVolume_Hot, self).teardown_method(method)

    def test_T5629_hot_vol_with_size(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_id, Size=20)
            check_volume(self.sshclient, self.dev, 20, with_format=False, text_to_check=self.text_to_check, no_create=True,
                         volume_type='io1', perf_iops=True, iops_io1=self.initial_iops, extend=True)
        except OscApiException as error:
            assert_oapi_error(error, 409, 'InvalidState', '6003')

    def test_T5630_hot_vol_with_iops(self):
        self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_id, Iops=400)
        check_volume(self.sshclient, self.dev, self.initial_size, with_format=False, text_to_check=self.text_to_check, no_create=True,
                     volume_type='io1', perf_iops=True, iops_io1=400, extend=True)

    def test_T5631_hot_vol_with_type(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_id, VolumeType='standard')
            check_volume(self.sshclient, self.dev, self.initial_size, with_format=False, text_to_check=self.text_to_check,
                         no_create=True, volume_type='standard', perf_iops=True, iops_io1=150, extend=True)
        except OscApiException as error:
            assert_oapi_error(error, 409, 'InvalidState', '6003')
