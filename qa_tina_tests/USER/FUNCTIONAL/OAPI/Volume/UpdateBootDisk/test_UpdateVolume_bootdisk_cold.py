
from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import oapi, wait, info_keys
from qa_tina_tools.tina.check_tools import verify_disk_size


class Test_UpdateVolume_bootdisk_cold(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateVolume_bootdisk_cold, cls).setup_class()
        cls.vm_info = None
        cls.vm_id = None
        cls.volume_id = None
        cls.sshclient = None
        cls.device_name = '/dev/vda1'
        cls.initial_size = 10
        cls.initial_iops = 150
        cls.known_error = False


    @classmethod
    def teardown_class(cls):
        super(Test_UpdateVolume_bootdisk_cold, cls).teardown_class()

    def setup_method(self, method):
        self.known_error = False
        super(Test_UpdateVolume_bootdisk_cold, self).setup_method(method)
        try:
            self.vm_info = oapi.create_Vms(self.a1_r1, state='ready')
            self.vm_id = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vm_info[info_keys.VM_IDS][0]]}).response.Vms[0]
            self.volume_id = self.vm_id.BlockDeviceMappings[0].Bsu.VolumeId

            self.sshclient = SshTools.check_connection_paramiko(ip_address=self.vm_info[info_keys.VMS][0]['PublicIp'],
                                                                ssh_key=self.vm_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                                username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

            verify_disk_size(self.sshclient, self.device_name, self.initial_size)

            oapi.stop_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], force=False)
        except:
            try:
                self.teardown_method(method)
            finally:
                raise

    def teardown_method(self, method):
        try:
            if self.vm_info:
                oapi.delete_Vms(self.a1_r1, self.vm_info)
        except Exception:
            if not self.known_error:
                raise
        finally:
            super(Test_UpdateVolume_bootdisk_cold, self).teardown_method(method)

    def test_T5799_update_vol_std_gp2(self):
        # Update volume size, and change volume type from standard to gp2
        self.a1_r1.oapi.UpdateVolume(VolumeId=self.volume_id, Size=15, VolumeType='gp2')

        try:
            oapi.start_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]])
        except AssertionError:
            known_error('TINA-6874', 'Vm in pending state when StartVms is called at the same time as UpdateVolume')

        ret = wait.wait_Vms_state(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], state='ready')
        public_ip = ret.response.Vms[0].PublicIp
        sshclient = SshTools.check_connection_paramiko(ip_address=public_ip,
                                                       ssh_key=self.vm_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                       username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

        verify_disk_size(sshclient, self.device_name, 15)

        oapi.stop_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], force=False)

        # Update volume size, and change volume type from gp2 to standard
        self.a1_r1.oapi.UpdateVolume(VolumeId=self.volume_id, Size=20, VolumeType='standard')

        try:
            oapi.start_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]])
        except AssertionError:
            known_error('TINA-6874', 'Vm in pending state when StartVms is called at the same time as UpdateVolume')

        ret = wait.wait_Vms_state(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], state='ready')
        public_ip = ret.response.Vms[0].PublicIp
        sshclient = SshTools.check_connection_paramiko(ip_address=public_ip,
                                                       ssh_key=self.vm_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                       username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

        verify_disk_size(sshclient, self.device_name, 20)

    def test_T5800_update_vol_std_io1(self):
        # Update volume size, and change volume type from standard to io1
        self.a1_r1.oapi.UpdateVolume(Iops=300, VolumeId=self.volume_id, Size=15, VolumeType='io1')

        try:
            oapi.start_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]])
        except AssertionError:
            known_error('TINA-6874', 'Vm in pending state when StartVms is called at the same time as UpdateVolume')

        ret = wait.wait_Vms_state(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], state='ready')
        public_ip = ret.response.Vms[0].PublicIp
        sshclient = SshTools.check_connection_paramiko(ip_address=public_ip,
                                                       ssh_key=self.vm_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                       username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

        verify_disk_size(sshclient, self.device_name, 15)

        oapi.stop_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], force=False)

        # Update volume size, and change volume type from io1 to standard
        self.a1_r1.oapi.UpdateVolume(VolumeId=self.volume_id, Size=20, VolumeType='standard')

        try:
            oapi.start_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]])
        except AssertionError:
            known_error('TINA-6874', 'Vm in pending state when StartVms is called at the same time as UpdateVolume')

        ret = wait.wait_Vms_state(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], state='ready')
        public_ip = ret.response.Vms[0].PublicIp
        sshclient = SshTools.check_connection_paramiko(ip_address=public_ip,
                                                       ssh_key=self.vm_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                       username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

        verify_disk_size(sshclient, self.device_name, 20)

    def test_T5801_update_vol_std_io1_gp2(self):
        # Update volume size, and change volume type from standard to io1
        self.a1_r1.oapi.UpdateVolume(Iops=300, VolumeId=self.volume_id, Size=15, VolumeType='io1')

        try:
            oapi.start_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]])
        except AssertionError:
            known_error('TINA-6874', 'Vm in pending state when StartVms is called at the same time as UpdateVolume')

        ret = wait.wait_Vms_state(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], state='ready')
        public_ip = ret.response.Vms[0].PublicIp
        sshclient = SshTools.check_connection_paramiko(ip_address=public_ip,
                                                       ssh_key=self.vm_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                       username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

        verify_disk_size(sshclient, self.device_name, 15)

        oapi.stop_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], force=False)

        # Update volume size, and change volume type from io1 to gp2
        self.a1_r1.oapi.UpdateVolume(VolumeId=self.volume_id, Size=20, VolumeType='gp2')

        try:
            oapi.start_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]])
        except AssertionError:
            known_error('TINA-6874', 'Vm in pending state when StartVms is called at the same time as UpdateVolume')

        ret = wait.wait_Vms_state(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], state='ready')
        public_ip = ret.response.Vms[0].PublicIp
        sshclient = SshTools.check_connection_paramiko(ip_address=public_ip,
                                                       ssh_key=self.vm_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                       username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

        verify_disk_size(sshclient, self.device_name, 20)

        oapi.stop_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], force=False)

        # Update volume size, and change volume type from gp2 to standard
        self.a1_r1.oapi.UpdateVolume(VolumeId=self.volume_id, Size=25, VolumeType='standard')

        try:
            oapi.start_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]])
        except AssertionError:
            known_error('TINA-6874', 'Vm in pending state when StartVms is called at the same time as UpdateVolume')

        ret = wait.wait_Vms_state(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], state='ready')
        public_ip = ret.response.Vms[0].PublicIp
        sshclient = SshTools.check_connection_paramiko(ip_address=public_ip,
                                                       ssh_key=self.vm_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                       username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

        verify_disk_size(sshclient, self.device_name, 25)
