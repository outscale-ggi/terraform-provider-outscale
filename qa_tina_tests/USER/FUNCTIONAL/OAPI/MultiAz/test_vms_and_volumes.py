import subprocess

from qa_test_tools.config import config_constants
from qa_test_tools.config.configuration import Configuration
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import info_keys, wait, oapi, check_tools
from qa_common_tools.ssh import SshTools


class Test_vms_and_volumes(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_vms_and_volumes, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_vms_and_volumes, cls).teardown_class()

    def test_T5677_create_vms_and_volumes(self):
        vm_info_a = None
        vm_info_b = None
        volume_a = None
        volume_b = None
        is_attached_volume_a = False
        is_attached_volume_b = False

        try:
            # create 2 instances with centos 7
            vm_info_a = oapi.create_Vms(self.a1_r1, az=self.a1_r1.config.region.name + "a")
            vm_info_b = oapi.create_Vms(self.a1_r1, az=self.a1_r1.config.region.name + "b")

            # create a security_group and authorize flux icmp with PrivateIp on vm_a and vm_b
            # self.a1_r1.oapi.CreateSecurityGroupRule(SecurityGroupId=vm_info_a[info_keys.SECURITY_GROUP_ID],
            #                                         IpProtocol='icmp',
            #                                         FromPortRange=-1, ToPortRange=-1,
            #                                         IpRange=vm_info_b[info_keys.VMS][0]["PrivateIp"]+"/32",
            #                                         Flow='Inbound')
            # self.a1_r1.oapi.CreateSecurityGroupRule(SecurityGroupId=vm_info_b[info_keys.SECURITY_GROUP_ID],
            #                                         IpProtocol='icmp',
            #                                         FromPortRange=-1, ToPortRange=-1,
            #                                         IpRange=vm_info_a[info_keys.VMS][0]["PrivateIp"]+"/32",
            #                                         Flow='Inbound')

            # create a security_group and authorize flux icmp with PublicIp on vm_a and vm_b
            self.a1_r1.oapi.CreateSecurityGroupRule(SecurityGroupId=vm_info_a[info_keys.SECURITY_GROUP_ID],
                                                    IpProtocol='icmp',
                                                    FromPortRange=-1, ToPortRange=-1,
                                                    IpRange=vm_info_b[info_keys.VMS][0]["PublicIp"]+"/32",
                                                    Flow='Inbound')
            self.a1_r1.oapi.CreateSecurityGroupRule(SecurityGroupId=vm_info_b[info_keys.SECURITY_GROUP_ID],
                                                    IpProtocol='icmp',
                                                    FromPortRange=-1, ToPortRange=-1,
                                                    IpRange=vm_info_a[info_keys.VMS][0]["PublicIp"]+"/32",
                                                    Flow='Inbound')
            # create 2 volumes
            volume_a = self.a1_r1.oapi.CreateVolume(Size=10,
                                                    SubregionName=self.a1_r1.config.region.name + "a").response.Volume
            volume_b = self.a1_r1.oapi.CreateVolume(Size=10,
                                                    SubregionName=self.a1_r1.config.region.name + "b").response.Volume

            # wait volumes are available
            wait.wait_Volumes_state(self.a1_r1, [volume_a.VolumeId, volume_b.VolumeId], state="available")

            # link volumes to vms
            self.a1_r1.oapi.LinkVolume(DeviceName="/dev/xvdb",
                                       VmId=vm_info_a[info_keys.VM_IDS][0], VolumeId=volume_a.VolumeId)

            wait.wait_Volumes_state(self.a1_r1, [volume_a.VolumeId], state="in-use")
            is_attached_volume_a = True
            self.a1_r1.oapi.LinkVolume(DeviceName="/dev/xvdb",
                                       VmId=vm_info_b[info_keys.VM_IDS][0], VolumeId=volume_b.VolumeId)
            wait.wait_Volumes_state(self.a1_r1, [volume_b.VolumeId], state="in-use")
            is_attached_volume_b = True

            wait.wait_Vms_state(self.a1_r1, [vm_info_a[info_keys.VM_IDS][0],
                                             vm_info_b[info_keys.VM_IDS][0]], state="ready")

            # connect to vms in ssh
            ssh_client_a = SshTools.check_connection_paramiko(vm_info_a[info_keys.VMS][0]["PublicIp"],
                                                                vm_info_a[info_keys.KEY_PAIR][info_keys.PATH],
                                                                username=self.a1_r1.config.region.get_info(
                                                                    config_constants.CENTOS_USER))
            ssh_client_b = SshTools.check_connection_paramiko(vm_info_b[info_keys.VMS][0]["PublicIp"],
                                                                vm_info_b[info_keys.KEY_PAIR][info_keys.PATH],
                                                                username=self.a1_r1.config.region.get_info(
                                                                    config_constants.CENTOS_USER))

            # check volumes
            check_tools.check_volume(ssh_client_a,"/dev/xvdb", 10)
            check_tools.check_volume(ssh_client_b,"/dev/xvdb", 10)

            # vm_a ping to internet
            google_ip = Configuration.get('ipaddress', 'dns_google')
            cmd = "ping " + google_ip + " -c 1"
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_a, cmd, retry=20)
            self.logger.info("vm_a ping to internet")
            self.logger.info(out)

            # vm_a ping to vm_b with public IP
            vm_b_public_ip = vm_info_b[info_keys.VMS][0]["PublicIp"]
            cmd = "ping " + vm_b_public_ip + " -c 1"
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_a, cmd, retry=20)
            self.logger.info("vm_a ping to vm_b with public IP")
            self.logger.info(out)

            #  vm_a ping to vm_b with private IP
            vm_b_private_ip = vm_info_b[info_keys.VMS][0]["PrivateIp"]
            cmd = "ping " + vm_b_private_ip + " -c 1"
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_a, cmd, retry=20)
            self.logger.info("vm_a ping to vm_b with private IP")
            self.logger.info(out)

            # vm_b ping to internet
            cmd = "ping " + google_ip + " -c 1"
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_b, cmd, retry=20)
            self.logger.info("vm_b ping to internet")
            self.logger.info(out)

            # vm_b ping to vm_a with public IP
            vm_a_public_ip = vm_info_a[info_keys.VMS][0]["PublicIp"]
            cmd = "ping " + vm_a_public_ip + " -c 1"
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_b, cmd, retry=20)
            self.logger.info("vm_b ping to vm_a with public IP")
            self.logger.info(out)

            # vm_b ping to vm_a with private IP
            vm_a_private_ip = vm_info_a[info_keys.VMS][0]["PrivateIp"]
            cmd = "ping " + vm_a_private_ip + " -c 1"
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_b, cmd, retry=20)
            self.logger.info("vm_b ping to vm_a with private IP")
            self.logger.info(out)

            # get DNS resolution google from vm a
            cmd1 = "sudo yum install -y bind-utils"
            cmd2 = "nslookup dns.google.com"
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_a, cmd1, timeout=300)
            self.logger.info(out)
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_a, cmd2, retry=20)
            self.logger.info("get DNS resolution google from instance a")
            self.logger.info(out)
            assert google_ip in out

            # get DNS resolution google from vm b
            cmd1 = "sudo yum install -y bind-utils"
            cmd2 = "nslookup dns.google.com"
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_b, cmd1)
            self.logger.info(out)
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_b, cmd2, retry=20, timeout=300)
            self.logger.info("get DNS resolution google from instance a")
            self.logger.info(out)
            assert google_ip in out

            # get vm b private dns name from vm a
            vm_b_private_dns_name = vm_info_b[info_keys.VMS][0]["PrivateDnsName"]
            cmd = "nslookup " + vm_b_private_dns_name
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_a, cmd, retry=20)
            self.logger.info("get instance private b name from instance a")
            self.logger.info(out)
            assert vm_b_private_ip in out

            # get vm b public dns name from vm a
            vm_b_public_dns_name = vm_info_b[info_keys.VMS][0]["PublicDnsName"]
            cmd = "nslookup " + vm_b_public_dns_name
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_a, cmd, retry=20)
            self.logger.info("get instance private b name from instance a")
            self.logger.info(out)
            assert vm_b_private_ip in out

            # get vm a private dns name from vm b
            vm_a_private_dns_name = vm_info_a[info_keys.VMS][0]["PrivateDnsName"]
            cmd = "nslookup " + vm_a_private_dns_name
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_b, cmd, retry=20)
            self.logger.info("get instance private a name from instance b")
            self.logger.info(out)
            assert vm_a_private_ip in out

            # get vm a public dns name from vm b
            vm_a_public_dns_name = vm_info_a[info_keys.VMS][0]["PublicDnsName"]
            cmd = "nslookup " + vm_a_public_dns_name
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_b, cmd, retry=20)
            self.logger.info("get instance private a name from instance b")
            self.logger.info(out)
            assert vm_a_private_ip in out

            # get vm a private dns name from internet
            cmd = "nslookup " + vm_a_private_dns_name
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            out, _ = proc.communicate()
            assert vm_a_private_ip in out.decode('utf-8')


            # get vm a public dns name from internet
            cmd = "nslookup " + vm_a_public_dns_name
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            out, _ = proc.communicate()
            assert vm_a_public_ip in out.decode('utf-8')

        finally:
            if is_attached_volume_a:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=volume_a.VolumeId)
            if is_attached_volume_b:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=volume_b.VolumeId)
            if volume_a:
                wait.wait_Volumes_state(self.a1_r1, [volume_a.VolumeId], state='available')
                self.a1_r1.oapi.DeleteVolume(VolumeId=volume_a.VolumeId)
                wait.wait_Volumes_state(self.a1_r1, [volume_a.VolumeId], cleanup=True)
            if volume_b:
                wait.wait_Volumes_state(self.a1_r1, [volume_b.VolumeId], state='available')
                self.a1_r1.oapi.DeleteVolume(VolumeId=volume_b.VolumeId)
                wait.wait_Volumes_state(self.a1_r1, [volume_b.VolumeId], cleanup=True)
            if vm_info_a:
                oapi.delete_Vms(self.a1_r1, vm_info_a, wait=True)
            if vm_info_b:
                oapi.delete_Vms(self.a1_r1, vm_info_b, wait=True)
