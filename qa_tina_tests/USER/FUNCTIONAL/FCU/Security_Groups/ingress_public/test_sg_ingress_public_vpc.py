import time
from platform import system as system_name

import subprocess
from subprocess import CalledProcessError
import pytest

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import setup_tools
from qa_tina_tools.tina.info_keys import NAME, PATH
from qa_tina_tools.tools.tina.create_tools import create_instances_old, create_keypair
from qa_tina_tools.tools.tina.delete_tools import delete_subnet, delete_instances_old, delete_keypair
from qa_tina_tools.tina import check_tools


def ping(host, retry=10, timeout=5):
    """
    Returns True if host (str) responds to a ping request.
    Remember that some hosts may not respond to a ping request even if the host name is valid.
    """

    # Ping parameters as function of OS
    # parameters = "-n 1" if system_name().lower() == "windows" else "-c 1"
    # Pinging
    # return system_call("ping " + parameters + " " + host) == 0
    count = 0
    args = ['ping -n 1 {}'.format(host)] if system_name().lower() == "windows" else ['ping -c 1 {}'.format(host)]
    while count < retry:
        try:
            subprocess.check_call(args, shell=True)
            return True
        except CalledProcessError:
            print("Ping Failed!")
        count += 1
        time.sleep(timeout)
        # return subprocess.run(args, stdout=subprocess.PIPE).returncode == 0
    return False

class Test_sg_ingress_public_vpc(OscTinaTest):
    """
        check that from a set of regions
        the others set regions are not available
    """

    @classmethod
    def setup_class(cls):
        super(Test_sg_ingress_public_vpc, cls).setup_class()
        cls.cidr = Configuration.get('cidr', 'allips')
        cls.kp_info = None
        cls.sg_id = None
        cls.sg_id1 = None
        cls.subnet1 = None
        cls.rtb1 = None
        cls.igw_id = None
        cls.subnet1_id = None
        cls.vpc_id = None
        cls.eip = None
        try:
            # allocate eip
            cls.eip = cls.a1_r1.fcu.AllocateAddress()

            # get allocationID
            ret = cls.a1_r1.fcu.DescribeAddresses(PublicIp=[cls.eip.response.publicIp])
            cls.eip_allo_id = ret.response.addressesSet[0].allocationId

            # create VPC
            vpc = cls.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc_id = vpc.response.vpc.vpcId

            # create subnet 1
            ret = cls.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_1_0_24'), VpcId=cls.vpc_id)
            cls.subnet1_id = ret.response.subnet.subnetId

            # create internetgateway
            ret = cls.a1_r1.fcu.CreateInternetGateway()
            cls.igw_id = ret.response.internetGateway.internetGatewayId

            ret = cls.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=cls.igw_id, VpcId=cls.vpc_id)

            # create route tables1
            ret = cls.a1_r1.fcu.CreateRouteTable(VpcId=cls.vpc_id)
            cls.rtb1 = ret.response.routeTable.routeTableId

            # accociate routetable 1
            ret = cls.a1_r1.fcu.AssociateRouteTable(RouteTableId=cls.rtb1, SubnetId=cls.subnet1_id)
            cls.rt_asso1_id = ret.response.associationId

            # add route RTB1
            ret = cls.a1_r1.fcu.CreateRoute(DestinationCidrBlock=cls.cidr, GatewayId=cls.igw_id, RouteTableId=cls.rtb1)

            # create keypair
            cls.kp_info = create_keypair(cls.a1_r1)

        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.igw_id:
                cls.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=cls.igw_id, VpcId=cls.vpc_id)
                cls.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=cls.igw_id)

            if cls.subnet1_id:
                delete_subnet(cls.a1_r1, cls.subnet1_id)

            if cls.rtb1:
                cls.a1_r1.fcu.DeleteRouteTable(RouteTableId=cls.rtb1)

            if cls.vpc_id:
                cls.a1_r1.fcu.DeleteVpc(VpcId=cls.vpc_id)

            if cls.eip:
                cls.a1_r1.fcu.ReleaseAddress(PublicIp=cls.eip.response.publicIp)

            if cls.kp_info:
                delete_keypair(cls.a1_r1, cls.kp_info)

        finally:
            super(Test_sg_ingress_public_vpc, cls).teardown_class()

    def create_instance(self, security_group_id=None, subnet_id=None):

        ret, id_list = create_instances_old(self.a1_r1, security_group_id_list=[security_group_id], subnet_id=subnet_id,
                                            key_name=self.kp_info[NAME], state='ready')
        inst_id = id_list[0]
        if subnet_id:
            self.a1_r1.fcu.AssociateAddress(AllocationId=self.eip_allo_id, InstanceId=id_list[0])
            public_ip_inst = self.eip.response.publicIp
        else:
            public_ip_inst = ret.response.reservationSet[0].instancesSet[0].ipAddress

        return inst_id, public_ip_inst

    def config_tftp(self, sshclient, text_to_check):

        setup_tools.install_python_3(sshclient)

        cmd = 'sudo python3 -m pip install --user --upgrade pip'
        out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
        self.logger.info(out)
        assert not status, "pip package was not upgrade correctly"

        cmd = 'sudo python3 -m pip install --no-warn-script-location ptftpd'
        out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
        self.logger.info(out)
        assert not status, "ptftpd package was not installed correctly"

        cmd = 'sudo touch /tmp/demo.txt'
        out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
        self.logger.info(out)
        assert not status

        cmd = 'sudo chmod 666 /tmp/demo.txt'
        out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
        self.logger.info(out)
        assert not status

        cmd = 'sudo echo \'{}\' > /tmp/demo.txt'.format(text_to_check)
        out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
        self.logger.info(out)
        assert not status

        try:
            # start the service
            cmd = 'nohup sudo sh -c "( ( sudo env "PATH=$PATH" ptftpd eth0 /tmp/ &> /dev/null < /dev/null ) & )"'
            out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
            self.logger.info(out)
            assert not status
        except Exception as error:
            print(error)

    def create_rules(self, sg_id):
        self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=sg_id, IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp=self.cidr)
        self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=sg_id, IpProtocol='icmp', FromPort=-1, ToPort=-1, CidrIp=self.cidr)
        self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=sg_id, IpProtocol='udp', FromPort=69, ToPort=69, CidrIp=self.cidr)

    def test_T23_sg_public_ingress(self):

        text_to_check = 'test_sg_group'
        sg_name = id_generator(prefix='sg_')
        inst_id = None
        sg_id = None

        try:
            # create security group
            sg_response = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name)
            sg_id = sg_response.response.groupId

            # authorize rules
            self.create_rules(sg_id)

            inst_id, public_ip_inst = self.create_instance(security_group_id=sg_id)

            # validate ICMP
            assert ping(host=public_ip_inst)

            sshclient = check_tools.check_ssh_connection(self.a1_r1, inst_id, public_ip_inst, self.kp_info[PATH],
                                                         self.a1_r1.config.region.get_info(constants.CENTOS_USER))

            cmd = 'pwd'
            _, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
            assert not status, "SSH command was not executed correctly on the remote host"

            # validate UDP
            self.config_tftp(sshclient=sshclient, text_to_check=text_to_check)

            args = ["tftp -v -m binary {} -c get demo.txt demo.out.txt".format(public_ip_inst)]
            try:
                subprocess.check_call(args, shell=True)
            except CalledProcessError as error:
                print('Could not execute command', error.output, error.returncode)
            finally:
                try:
                    demo_file = open('demo.out.txt', 'r')
                except FileNotFoundError:
                    print('Could not open/read file:', demo_file)
                finally:
                    lines = demo_file.readlines()
                    assert lines[0].strip() == text_to_check

        finally:
            try:
                if inst_id:
                    try:
                        delete_instances_old(self.a1_r1, [inst_id])
                    except Exception:
                        print('Could not delete instances')

                if sg_id:
                    try:
                        self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                    except Exception:
                        print('Could not delete security group')

            except:
                pytest.fail("An error happened deleting resources in the test")

    def test_T37_sg_vpc_ingress(self):

        text_to_check = 'test_sg_group'
        sg_name_vpc = id_generator(prefix='sg_')
        inst_id = None
        sg_id = None

        try:

            sg_response = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description_vpc',
                                                             GroupName=sg_name_vpc, VpcId=self.vpc_id)
            sg_id = sg_response.response.groupId

            # authorize rules
            self.create_rules(sg_id)

            inst_id, public_ip_inst = self.create_instance(security_group_id=sg_id, subnet_id=self.subnet1_id)

            # validate ICMP
            assert ping(host=public_ip_inst)

            sshclient = check_tools.check_ssh_connection(self.a1_r1, inst_id, public_ip_inst, self.kp_info[PATH],
                                                         self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # validate tcp
            cmd = 'pwd'
            _, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
            assert not status, "SSH command was not executed correctly on the remote host"

            # validate UDP
            self.config_tftp(sshclient=sshclient, text_to_check=text_to_check)

            args = ["tftp -v -m binary {} -c get demo.txt demo.out.txt".format(public_ip_inst)]
            try:
                subprocess.check_call(args, shell=True)
            except CalledProcessError as error:
                print('Could not execute command', error.output, error.returncode)
            finally:
                try:
                    demo_file = open('demo.out.txt', 'r')
                except FileNotFoundError:
                    print('Could not open/read file:', demo_file)
                finally:
                    lines = demo_file.readlines()
                    assert lines[0].strip() == text_to_check

        finally:
            try:
                if inst_id:
                    try:
                        delete_instances_old(self.a1_r1, [inst_id])
                    except Exception:
                        print('Could not delete instances')

                if sg_id:
                    try:
                        self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                    except Exception:
                        print('Could not delete security group')

            except:
                pytest.fail("An error happened deleting resources in the test")
