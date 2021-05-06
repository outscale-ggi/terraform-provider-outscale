import uuid

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import oapi, wait, info_keys
from qa_tina_tools.tina.check_tools import check_volume
from qa_tina_tools.tina.wait import wait_Volumes_state


class Test_UpdateVolume_warm(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateVolume_warm, cls).setup_class()
        cls.vm_info = None
        cls.linked = None
        cls.vol_id = None
        cls.sshclient = None
        cls.text_to_check = None
        cls.initial_size = 10
        cls.dev = '/dev/xvdc'
        cls.initial_iops = 200
        cls.kp_path = None

    @classmethod
    def teardown_class(cls):
        super(Test_UpdateVolume_warm, cls).teardown_class()

    def setup_method(self, method):
        # tu pars du principe qu'elle est démarrée ..
        super(Test_UpdateVolume_warm, self).setup_method(method)
        self.vol_id = None
        self.linked = None
        self.sshclient = None
        self.text_to_check = None
        self.kp_path = None
        try:
            self.vm_info = oapi.create_Vms(self.a1_r1, state='running')
            self.kp_path = self.vm_info[info_keys.KEY_PAIR][info_keys.PATH]
            az_name = self.a1_r1.config.region.az_name
            initial_size = 10
            self.vol_id = self.a1_r1.oapi.CreateVolume(VolumeType='io1', Size=initial_size, Iops=self.initial_iops,
                                                       SubregionName=az_name).response.Volume.VolumeId
            wait_Volumes_state(self.a1_r1, [self.vol_id], 'available')
            self.linked = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id, VmId=self.vm_info[info_keys.VM_IDS][0],
                                                     DeviceName=self.dev)
            wait_Volumes_state(self.a1_r1, [self.vol_id], 'in-use')

            wait.wait_Vms_state(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], state='ready')
            self.sshclient = SshTools.check_connection_paramiko(self.vm_info[info_keys.VMS][0]['PublicIp'], self.kp_path,
                                                                username=self.a1_r1.config.region.get_info(
                                                                    constants.CENTOS_USER))

            self.text_to_check = uuid.uuid4().hex
            check_volume(self.sshclient, dev=self.dev, size=self.initial_size, text_to_check=self.text_to_check,
                         volume_type='io1', iops_io1=self.initial_iops)

            oapi.stop_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], force=False)

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
            if self.vm_info:
                oapi.delete_Vms(self.a1_r1, self.vm_info)
        finally:
            super(Test_UpdateVolume_warm, self).teardown_method(method)

    def test_T5626_warm_vol_with_size(self):
        self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_id, Size=20)

        oapi.start_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]])
        ret = wait.wait_Vms_state(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], state='ready')
        public_ip = ret.response.Vms[0].PublicIp
        self.sshclient = SshTools.check_connection_paramiko(public_ip, self.kp_path,
                                                            username=self.a1_r1.config.region.get_info(
                                                                constants.CENTOS_USER))

        check_volume(self.sshclient, self.dev, 20, with_format=False, text_to_check=self.text_to_check, no_create=True,
                     volume_type='io1', perf_iops=True, iops_io1=self.initial_iops, extend=True)

    def test_T5627_warm_vol_with_iops(self):
        self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_id, Iops=400)

        oapi.start_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]])
        ret = wait.wait_Vms_state(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], state='ready')
        public_ip = ret.response.Vms[0].PublicIp
        self.sshclient = SshTools.check_connection_paramiko(public_ip, self.kp_path,
                                                            username=self.a1_r1.config.region.get_info(
                                                                constants.CENTOS_USER))

        check_volume(self.sshclient, self.dev, self.initial_size, with_format=False, text_to_check=self.text_to_check, no_create=True,
                     volume_type='io1', perf_iops=True, iops_io1=400, extend=True)

    def test_T5628_warm_vol_with_type(self):
        self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_id, VolumeType='standard')

        oapi.start_Vms(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]])
        ret = wait.wait_Vms_state(self.a1_r1, [self.vm_info[info_keys.VM_IDS][0]], state='ready')
        public_ip = ret.response.Vms[0].PublicIp
        self.sshclient = SshTools.check_connection_paramiko(public_ip, self.kp_path,
                                                            username=self.a1_r1.config.region.get_info(
                                                                constants.CENTOS_USER))

        check_volume(self.sshclient, self.dev, self.initial_size, with_format=False, text_to_check=self.text_to_check,
                     no_create=True, volume_type='standard', perf_iops=True, iops_io1=150, extend=True)
