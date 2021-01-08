import pytest

from qa_common_tools.ssh import SshTools, OscCommandError
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.config.region import Feature
from qa_test_tools.test_base import known_error
from qa_tina_tests.USER.FUNCTIONAL.FCU.Instances.Linux.linux_instance import Test_linux_instance
from qa_tina_tools.tina import check_tools
from qa_tina_tools.tina.check_tools import check_volume
from qa_tina_tools.tina.info_keys import PATH
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


# EPH_TYPES = ['m3.medium', 'm3.large', 'm3.xlarge', 'm3.2xlarge', 'r3.large', 'r3.xlarge', 'r3.2xlarge', 'r3.4xlarge', 'r3.8xlarge', 'g2.2xlarge',
#              'mv3.large', 'mv3.xlarge', 'mv3.2xlarge', 'og4.xlarge', 'og4.2xlarge', 'og4.4xlarge', 'og4.8xlarge', 'io5.2xlarge', 'io5.4xlarge',
#              'io5.6xlarge', 'io5.8xlarge', 'io5.12xlarge', 'io5.18xlarge']
EPH_TYPES = ['r3.2xlarge']


class Test_public_linux_instance(Test_linux_instance):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'gpu_limit': 4}
        cls.GROUPS = ['PRODUCTION', 'NVIDIA']
        super(Test_public_linux_instance, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_public_linux_instance, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T61_create_use_linux_instance(self):
        inst_id = None
        try:
            inst_id, inst_public_ip = self.create_instance()
            if inst_id:
                sshclient = check_tools.check_ssh_connection(self.a1_r1, inst_id, inst_public_ip, self.kp_info[PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
                # sshclient = SshTools.check_connection_paramiko(inst_public_ip, self.kp_info[PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
                cmd = 'pwd'
                out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
                self.logger.info(out)
                assert not status, "SSH command was not executed correctly on the remote host"
                if Feature.INTERNET in self.a1_r1.config.region.get_info(constants.FEATURES):
                    target_ip = Configuration.get('ipaddress', 'dns_google')
                else:
                    target_ip = '.'.join(inst_public_ip.split('.')[:-1]) + '.254'
                cmd = "ping " + target_ip + " -c 1"
                out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
                self.logger.info(out)
                # check ping google DNS
                assert not status, "Instance not connected to internet"

                if Feature.INTERNET in self.a1_r1.config.region.get_info(constants.FEATURES):
                    cmd = "ping google.com -c 1"
                    out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
                    self.logger.info(out)
                    assert not status, "Instance could not resolve google.com"

        finally:
            if inst_id:
                delete_instances_old(self.a1_r1, [inst_id])

    @pytest.mark.tag_redwire
    @pytest.mark.region_gpu
    def test_T98_create_use_linux_GPU_instance(self):
        Instance_Type='mv3.large'
        if self.a1_r1.config.region.name in ['cn-southeast-1']:
            Instance_Type = 'og4.xlarge'
        inst_id = None
        try:
            inst_id, inst_public_ip = self.create_instance(Instance_Type=Instance_Type)
            if inst_id:
                sshclient = check_tools.check_ssh_connection(self.a1_r1, inst_id, inst_public_ip, self.kp_info[PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
                # sshclient = SshTools.check_connection_paramiko(inst_public_ip, self.kp_info[PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
                cmd = 'sudo pwd'
                out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
                self.logger.info(out)
                assert not status, "SSH command was not executed correctly on the remote host"
                cmd = 'sudo yum install pciutils -y'
                out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=300)
                self.logger.info(out)
                assert not status, "SSH command was not executed correctly on the remote host"
                cmd = 'sudo lspci | grep -c NVIDIA '
                out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
                self.logger.info(out)
                assert not status, "SSH command was not executed correctly on the remote host"
        finally:
            if inst_id:
                delete_instances_old(self.a1_r1, [inst_id])

    @pytest.mark.tag_redwire
    @pytest.mark.region_dedicated
    def test_T103_create_use_linux_dedicated_instance(self):
        inst_id = None
        try:
            inst_id, inst_public_ip = self.create_instance(dedicated=True)
            if inst_id:
                sshclient = check_tools.check_ssh_connection(self.a1_r1, inst_id, inst_public_ip, self.kp_info[PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
                # sshclient = SshTools.check_connection_paramiko(inst_public_ip, self.kp_info[PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
                cmd = 'pwd'
                out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
                self.logger.info(out)
                assert not status, "SSH command was not executed correctly on the remote host"
        finally:
            if inst_id:
                delete_instances_old(self.a1_r1, [inst_id])

    @pytest.mark.tag_redwire
    def test_T119_create_start_stop_use_linux_instance(self):
        inst_id = None
        try:
            inst_id, _ = self.create_instance()
            if inst_id:
                self.a1_r1.fcu.StopInstances(InstanceId=[inst_id])
                wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[inst_id], state='stopped')
                self.a1_r1.fcu.StartInstances(InstanceId=inst_id)
                # wait instance to become ready check for login page
                wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[inst_id], state='ready')
                # get public IP

                describe_res = self.a1_r1.fcu.DescribeInstances(Filter=[{'Name': 'instance-id', 'Value': [inst_id]}])
                public_ip_inst = describe_res.response.reservationSet[0].instancesSet[0].ipAddress

                sshclient = check_tools.check_ssh_connection(self.a1_r1, inst_id, public_ip_inst, self.kp_info[PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
                # sshclient = SshTools.check_connection_paramiko(public_ip_inst, self.kp_info[PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

                cmd = 'pwd'
                out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
                self.logger.info(out)
                assert not status, "SSH command was not executed correctly on the remote host"

        finally:
            if inst_id:
                delete_instances_old(self.a1_r1, [inst_id])

    @pytest.mark.tag_redwire
    def test_T120_create_reboot_linux_instance(self):
        inst_id = None
        try:

            inst_id, _ = self.create_instance()

            if inst_id:

                self.a1_r1.fcu.RebootInstances(InstanceId=[inst_id])

                # wait instance to become ready check for login page
                describe_res = wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[inst_id], state='ready')

                inst_public_ip = describe_res.response.reservationSet[0].instancesSet[0].ipAddress

                sshclient = check_tools.check_ssh_connection(self.a1_r1, inst_id, inst_public_ip, self.kp_info[PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
                # sshclient = SshTools.check_connection_paramiko(inst_public_ip, self.kp_info[PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

                out, status, _ = SshTools.exec_command_paramiko(sshclient, 'pwd')
                self.logger.info(out)
                assert not status, "SSH command was not executed correctly on the remote host"

        finally:
            if inst_id:
                delete_instances_old(self.a1_r1, [inst_id])

    def test_T185_create_instance_with_ebs(self):
        inst_id = None
        device_name = '/dev/xvdb'
        size = 1
        ebs = {'DeleteOnTermination': 'true', 'VolumeSize': str(size), 'VolumeType': 'standard'}
        BlockDevice = [{'DeviceName': device_name, 'Ebs': ebs}]

        try:

            inst_id, inst_public_ip = self.create_instance(Instance_Type='t2.small', BlockDeviceMapping=BlockDevice)
            if inst_id:

                sshclient = SshTools.check_connection_paramiko(inst_public_ip, self.kp_info[PATH],
                                                               username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

                check_volume(sshclient, device_name, size, perf_iops=2, volume_type='standard')

        finally:
            if inst_id:
                delete_instances_old(self.a1_r1, [inst_id])

#     def test_TXXX_create_instance_with_ebs(self):
#         inst_id = None
#         device_name = '/dev/xvdb'
#         size = 1000
#         iops = 5000
#         v_type = 'io1'
#         ebs = {'DeleteOnTermination': 'true', 'VolumeSize': str(size), 'VolumeType': v_type, 'Iops': iops}
#         BlockDevice = [{'DeviceName': device_name, 'Ebs': ebs}]
#
#         try:
#
#             inst_id, inst_public_ip = self.create_instance(Instance_Type='t2.small', BlockDeviceMapping=BlockDevice)
#             if inst_id:
#
#                 sshclient = SshTools.check_connection_paramiko(inst_public_ip, self.kp_info[PATH],
#                                                                username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
#
#                 check_volume(sshclient, device_name, size, perf_iops=1, volume_type=v_type, iops_io1=iops)
#
#         finally:
#             if inst_id:
#                 delete_instances_old(self.a1_r1, [inst_id])

    @pytest.mark.tag_redwire
    @pytest.mark.region_ephemeral
    def test_T123_create_instance_linux_ephemeral(self):
        inst_id = None
        device_name = '/dev/xvdc'
        # size = 128
        size = 32
        BlockDevice = [{'DeviceName': device_name, 'VirtualName': 'ephemeral0'}]
        placement = None
        if self.a1_r1.config.region.az_name == 'cn-southeast-1a':
            placement = {'AvailabilityZone': 'cn-southeast-1b'}
        try:
            inst_id, inst_public_ip = self.create_instance(Instance_Type='r3.large', BlockDeviceMapping=BlockDevice, placement=placement)
            if inst_id:
                sshclient = check_tools.check_ssh_connection(self.a1_r1, inst_id, inst_public_ip, self.kp_info[PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
                # sshclient = SshTools.check_connection_paramiko(inst_public_ip, self.kp_info[PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
                check_volume(sshclient, device_name, size, with_format=False)
        except OscApiException as error:
            raise error
        finally:
            if inst_id:
                delete_instances_old(self.a1_r1, [inst_id])

    @pytest.mark.region_ephemeral
    def test_T5131_create_instance_linux_ephemeral1(self):
        inst_id = None
        device_name = '/dev/xvdc'
        # size = 128
        size = 32
        BlockDevice = [{'DeviceName': device_name, 'VirtualName': 'ephemeral1'}]
        placement = None
        if self.a1_r1.config.region.az_name == 'cn-southeast-1a':
            placement = {'AvailabilityZone': 'cn-southeast-1b'}
        try:
            inst_id, inst_public_ip = self.create_instance(Instance_Type='r3.large', BlockDeviceMapping=BlockDevice,
                                                           placement=placement)
            if inst_id:
                sshclient = SshTools.check_connection_paramiko(inst_public_ip, self.kp_info[PATH],
                                                               username=self.a1_r1.config.region.get_info(
                                                                   constants.CENTOS_USER))
                check_volume(sshclient, device_name, size, with_format=False)
                assert False, 'remove known error'
        except OscCommandError as error:
            if error.msg.startswith('Could not execute command : sudo mount /dev/xvdc /mnt/volume_'):
                known_error('TINA-5905', 'ephemeral different than ephemeral0 bug')
            raise error
        finally:
            if inst_id:
                delete_instances_old(self.a1_r1, [inst_id])

#     def test_TXXX(self):
#         inst_id = None
#         device_name = '/dev/xvdb'
#         #size = 128
#         size = 32
#         BlockDevice = [{'DeviceName': device_name, 'VirtualName': 'ephemeral0'}]
#         placement = None
#         if self.a1_r1.config.region.az_name == 'cn-southeast-1a':
#             placement = {'AvailabilityZone': 'cn-southeast-1b'}
#         results = {}
#         for typ in EPH_TYPES:
#             inst_id = None
#             try:
#                 print('Testing type {}'.format(typ))
#                 inst_id, inst_public_ip = self.create_instance(Instance_Type=typ, BlockDeviceMapping=BlockDevice, placement=placement)
#                 if inst_id:
#
#                     sshclient = SshTools.check_connection_paramiko(inst_public_ip, self.kp_info[PATH],
#                                                                    username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
#
#                     check_volume(sshclient, device_name, size, with_format=False)
#                 results[typ] = 'OK'
#             except Exception:
#                 results[typ] = 'KO'
#             finally:
#                 if inst_id:
#                     try:
#                         delete_instances_old(self.a1_r1, [inst_id])
#                     except:
#                         pass
#         print(results)
