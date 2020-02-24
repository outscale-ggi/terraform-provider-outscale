import pytest
from qa_common_tools.config import config_constants as constants

from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import PATH, INSTANCE_SET, KEY_PAIR
from qa_common_tools.ssh import SshTools


@pytest.mark.region_gpu
class Test_create_verify_gpu_instances(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'gpu_limit': 4}
        super(Test_create_verify_gpu_instances, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_create_verify_gpu_instances, cls).teardown_class()

    def verify_instance_type(self, inst_info, total_gpu, vcores, memory_ram):
        sshclient = SshTools.check_connection_paramiko(inst_info[INSTANCE_SET][0]['ipAddress'], inst_info[KEY_PAIR][PATH],
                                                       username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        cmd = 'sudo nproc'
        out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
        self.logger.info(out)
        assert not status, "SSH command was not executed correctly on the remote host"
        assert out.strip() == str(vcores), "Amount of cores does not match specifications for this type of instances"
        cmd = "sudo dmidecode -t 16 | grep 'Maximum Capacity' | awk '{print $3}'"
        out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
        self.logger.info(out)
        assert not status, "SSH command was not executed correctly on the remote host"
        assert out.strip() == str(memory_ram), "Memory does not match specifications for this type of instance"
        cmd = 'sudo yum install pciutils -y'
        out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
        self.logger.info(out)
        assert not status, "SSH command was not executed correctly on the remote host"
        cmd = 'sudo lspci | grep -c NVIDIA'
        out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
        self.logger.info(out)
        assert out.strip() == str(total_gpu), "The total GPU does not match "

    def test_T1395_create_and_verify_og4_xlarge(self):
        inst_info = None
        try:
            inst_info = create_instances(self.a1_r1, inst_type='og4.xlarge', state='ready')
            self.verify_instance_type(inst_info, total_gpu=1, vcores=8, memory_ram=61)
        finally:
            # terminate the instance
            if inst_info:
                try:
                    delete_instances(self.a1_r1, inst_info)
                except Exception as error:
                    pytest.fail('unexpected error while cleaning : ' + str(error))

    def test_T1396_create_and_verify_og4_2xlarge(self):
        inst_info = None
        try:
            inst_info = create_instances(self.a1_r1, inst_type='og4.2xlarge', state='ready')
            self.verify_instance_type(inst_info, total_gpu=2, vcores=16, memory_ram=123)
        finally:
            # terminate the instance
            if inst_info:
                try:
                    delete_instances(self.a1_r1, inst_info)
                except Exception as error:
                    pytest.fail('unexpected error while cleaning : ' + str(error))

    def test_T1397_create_and_verify_og4_4xlarge(self):
        inst_info = None
        try:
            if self.a1_r1.config.region.name.startswith('in'):
                ret = self.a1_r1.intel.slot.find_server_resources(hw_groups=['NVIDIA'])
                found = False
                for kvm in ret.response.result:
                    if not hasattr(kvm.available_gpus, 'nvidia_k2'):
                        continue
                    if len(getattr(kvm.available_gpus, 'nvidia_k2')) < 3:
                        continue
                    if kvm.available_memory < 184*pow(1024, 3):
                        continue
                    if kvm.available_core < 24:
                        continue
                    found = True
                    break
                if not found:
                    pytest.skip("No kvm available for og4.4xlarge")
            inst_info = create_instances(self.a1_r1, inst_type='og4.4xlarge', state='ready')
            self.verify_instance_type(inst_info, total_gpu=3, vcores=24, memory_ram=184)
        finally:
            # terminate the instance
            if inst_info:
                try:
                    delete_instances(self.a1_r1, inst_info)
                except Exception as error:
                    pytest.fail('unexpected error while cleaning : ' + str(error))

#     def test_T4266_create_and_verify_og4_8xlarge(self):
#         inst_info = None
#         try:
#             inst_info = create_instances(self.a1_r1, inst_type='og4.8xlarge', state='ready')
#             self.verify_instance_type(inst_info, total_gpu=4, vcores=32, memory_ram=240)
#         finally:
#             # terminate the instance
#             if inst_info:
#                 try:
#                     delete_instances(self.a1_r1, inst_info)
#                 except Exception as error:
#                     pytest.fail('unexpected error while cleaning : ' + str(error))
