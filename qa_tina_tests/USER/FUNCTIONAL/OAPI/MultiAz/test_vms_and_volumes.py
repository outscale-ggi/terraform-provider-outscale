from qa_test_tools.config import config_constants
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import info_keys, wait, oapi, check_tools
from qa_common_tools.ssh import SshTools, OscSshError


class Test_vms_and_volumes(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_vms_and_volumes, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_vms_and_volumes, cls).teardown_class()

    def test_T5677_create_vms_and_volumes(self):
        vm_info_a = None
        vm_info_b = None

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
            self.a1_r1.oapi.LinkVolume(DeviceName="/dev/xvdb",
                                       VmId=vm_info_b[info_keys.VM_IDS][0], VolumeId=volume_b.VolumeId)

            # wait volumes and vms state
            wait.wait_Volumes_state(self.a1_r1, [volume_a.VolumeId, volume_b.VolumeId], state="in-use")
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
            target_ip = Configuration.get('ipaddress', 'dns_google')
            cmd = "ping " + target_ip + " -c 1"
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_a, cmd, retry=20)
            self.logger.info("vm_a ping to internet")
            self.logger.info(out)

            # vm_a ping to vm_b with public IP
            vm_b_ip = vm_info_b[info_keys.VMS][0]["PublicIp"]
            cmd = "ping " + vm_b_ip + " -c 1"
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_a, cmd, retry=20)
            self.logger.info("vm_a ping to vm_b with public IP")
            self.logger.info(out)

            #  vm_a ping to vm_b with private IP
            vm_b_ip = vm_info_b[info_keys.VMS][0]["PrivateIp"]
            cmd = "ping " + vm_b_ip + " -c 1"
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_a, cmd, retry=20)
            self.logger.info("vm_a ping to vm_b with private IP")
            self.logger.info(out)

            # vm_b ping to internet
            target_ip = Configuration.get('ipaddress', 'dns_google')
            cmd = "ping " + target_ip + " -c 1"
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_b, cmd, retry=20)
            self.logger.info("vm_b ping to internet")
            self.logger.info(out)

            # vm_b ping to vm_a with public IP
            vm_a_ip = vm_info_a[info_keys.VMS][0]["PublicIp"]
            cmd = "ping " + vm_a_ip + " -c 1"
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_b, cmd, retry=20)
            self.logger.info("vm_b ping to vm_a with public IP")
            self.logger.info(out)

            # vm_b ping to vm_a with private IP
            vm_a_ip = vm_info_a[info_keys.VMS][0]["PrivateIp"]
            cmd = "ping " + vm_a_ip + " -c 1"
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_b, cmd, retry=20)
            self.logger.info("vm_b ping to vm_a with private IP")
            self.logger.info(out)

            # get DNS resolution google from instance a
            target_ip = Configuration.get('ipaddress', 'dns_google')
            cmd1 = "sudo yum install -y bind-utils"
            cmd2 = "nslookup " + target_ip
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_a, cmd1, retry=20)
            self.logger.info(out)
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_a, cmd2, retry=20)
            self.logger.info("get DNS resolution google from instance a")
            self.logger.info(out)

            # get DNS resolution google from instance b
            target_ip = Configuration.get('ipaddress', 'dns_google')
            cmd1 = "sudo yum install -y bind-utils"
            cmd2 = "nslookup " + target_ip
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_b, cmd1, retry=20)
            self.logger.info(out)
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_b, cmd2, retry=20)
            self.logger.info("get DNS resolution google from instance b")
            self.logger.info(out)

            # get instance private b name from instance a
            vm_b_ip = vm_info_b[info_keys.VMS][0]["PrivateIp"]
            cmd = "nslookup " + vm_b_ip
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_a, cmd, retry=20)
            self.logger.info("get instance private b name from instance a")
            self.logger.info(out)
            instance_private_b_name = "ip-" + vm_b_ip.replace(".","-") + ".in-west-1.compute.internal"
            assert instance_private_b_name in out

            # # get instance public b name from instance a
            vm_b_ip = vm_info_b[info_keys.VMS][0]["PublicIp"]
            cmd = "nslookup " + vm_b_ip
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_a, cmd, retry=20)
            self.logger.info("get instance private b name from instance a")
            self.logger.info(out)
            instance_private_b_name = "ip-" + vm_b_ip.replace(".","-") + ".in-west-1.compute.internal"
            assert instance_private_b_name in out

            # # get instance private a name from instance b
            vm_a_ip = vm_info_a[info_keys.VMS][0]["PrivateIp"]
            cmd = "nslookup " + vm_a_ip
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_b, cmd, retry=20)
            self.logger.info("get instance private a name from instance b")
            self.logger.info(out)
            instance_private_a_name = "ip-" + vm_a_ip.replace(".","-") + ".in-west-1.compute.internal"
            assert instance_private_a_name in out

            # # get instance public z name from instance b
            vm_a_ip = vm_info_a[info_keys.VMS][0]["PublicIp"]
            cmd = "nslookup " + vm_a_ip
            out, _, _ = SshTools.exec_command_paramiko(ssh_client_b, cmd, retry=20)
            self.logger.info("get instance private a name from instance b")
            self.logger.info(out)
            instance_private_a_name = "ip-" + vm_a_ip.replace(".","-") + ".in-west-1.compute.internal"
            assert instance_private_a_name in out

        except OscSshError:
            self.logger.info('OscSshError')

        finally:
            try:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=volume_a.VolumeId)
            except:
                self.logger.debug('Could not unlink volume_a')
            try:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=volume_b.VolumeId)
            except:
                self.logger.debug('Could not unlink volume_b')
            if volume_a:
                wait.wait_Volumes_state(self.a1_r1, [volume_a.VolumeId], state='available')
                self.a1_r1.oapi.DeleteVolume(VolumeId=volume_a.VolumeId)
            if volume_b:
                wait.wait_Volumes_state(self.a1_r1, [volume_b.VolumeId], state='available')
                self.a1_r1.oapi.DeleteVolume(VolumeId=volume_b.VolumeId)
            if vm_info_a:
                oapi.delete_Vms(self.a1_r1, vm_info_a, wait=True)
            if vm_info_b:
                oapi.delete_Vms(self.a1_r1, vm_info_b, wait=True)
