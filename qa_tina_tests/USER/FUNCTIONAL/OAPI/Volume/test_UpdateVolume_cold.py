import uuid

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import oapi, wait, info_keys
from qa_tina_tools.tina.check_tools import check_volume
from qa_tina_tools.tina.wait import wait_Volumes_state, wait_Vms_state


class Test_UpdateVolume_Cold(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateVolume_Cold, cls).setup_class()
        cls.vm_info = None
        cls.vol_id = None
        cls.sshclient = None
        cls.dev = '/dev/xvdc'
        cls.initial_size = 10
        cls.text_to_check = None
        cls.is_attached = False
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
                cls.a1_r1.oapi.DeleteVms(VmIds=[cls.vm_info[info_keys.VM_IDS][0]])
                wait_Vms_state(cls.a1_r1, [cls.vm_info[info_keys.VM_IDS][0]], state='terminated')
        finally:
            super(Test_UpdateVolume_Cold, cls).teardown_class()

    def setup_method(self, method):
        super(Test_UpdateVolume_Cold, self).setup_method(method)
        self.vol_id = None
        self.sshclient = None
        self.text_to_check = None
        self.is_attached = False
        try:
            # Create Volume
            kp_path = self.vm_info[info_keys.KEY_PAIR][info_keys.PATH]
            az_name = self.a1_r1.config.region.az_name
            self.vol_id = self.a1_r1.oapi.CreateVolume(VolumeType='io1', Size=self.initial_size, Iops=200,
                                                       SubregionName=az_name).response.Volume.VolumeId
            wait_Volumes_state(self.a1_r1, [self.vol_id], 'available')
            self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id, VmId=self.vm_info[info_keys.VM_IDS][0],
                                                     DeviceName=self.dev)
            wait_Volumes_state(self.a1_r1, [self.vol_id], 'in-use')
            self.is_attached = True
            wait.wait_Vms_state(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], state='ready')
            vm_ip = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vm_info[info_keys.VM_IDS][0]]}).response.Vms[
                0].PublicIp
            self.sshclient = SshTools.check_connection_paramiko(vm_ip, kp_path,
                                                                username=self.a1_r1.config.region.get_info(
                                                                    constants.CENTOS_USER))
            self.text_to_check = uuid.uuid4().hex
            check_volume(self.sshclient, dev=self.dev, size=self.initial_size, text_to_check=self.text_to_check,
                         volume_type='io1', iops_io1=200)

            self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id)
            wait_Volumes_state(self.a1_r1, [self.vol_id], 'available')
            self.is_attached = False

        except Exception as error:
            try:
                self.teardown_method(method)
            except Exception as err:
                raise err
            finally:
                raise error

    def teardown_method(self, method):
        try:
            if self.is_attached:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id)
                wait_Volumes_state(self.a1_r1, [self.vol_id], 'available')
            if self.vol_id:
                self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol_id)
        finally:
            super(Test_UpdateVolume_Cold, self).teardown_method(method)

    def test_T9999_cold_vol_with_size(self):
        self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_id, Size=20)
        self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id, VmId=self.vm_info[info_keys.VM_IDS][0],
                                                 DeviceName=self.dev)
        wait_Volumes_state(self.a1_r1, [self.vol_id], 'in-use')
        self.is_attached = True

        check_volume(self.sshclient, self.dev, 20, with_format=False, text_to_check=self.text_to_check, no_create=True,
                     volume_type='io1', iops_io1=200)

    def test_T9999_cold_vol_with_iops(self):
        self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_id, Iops=400)
        self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id, VmId=self.vm_info[info_keys.VM_IDS][0],
                                                 DeviceName=self.dev)
        wait_Volumes_state(self.a1_r1, [self.vol_id], 'in-use')
        self.is_attached = True
        check_volume(self.sshclient, self.dev, self.initial_size, with_format=False, text_to_check=self.text_to_check,
                     no_create=True,
                     volume_type='io1', perf_iops=True, iops_io1=400)

    def test_T9999_cold_vol_with_type(self):
        self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_id, VolumeType='standard')
        self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id, VmId=self.vm_info[info_keys.VM_IDS][0],
                                                 DeviceName=self.dev)
        wait_Volumes_state(self.a1_r1, [self.vol_id], 'in-use')
        self.is_attached = True
        check_volume(self.sshclient, self.dev, self.initial_size, with_format=False, text_to_check=self.text_to_check,
                     no_create=True, volume_type='standard', perf_iops=True, iops_io1=200)
