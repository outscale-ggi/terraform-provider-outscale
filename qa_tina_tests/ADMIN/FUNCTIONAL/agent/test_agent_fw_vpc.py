import os

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_common_tools.ssh import SshTools
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.config import config_constants as constants
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_tina_tools.tools.tina.info_keys import ROUTE_TABLE_ID, SUBNETS, SUBNET_ID, INSTANCE_ID_LIST, INTERNET_GATEWAY_ID, SECURITY_GROUP_ID
from qa_tina_tools.tools.tina.info_keys import KEY_PAIR, PATH, INSTANCE_SET, VPC_ID
from netaddr import IPNetwork, IPAddress


class Test_agent_fw_vpc(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_agent_fw_vpc, cls).setup_class()
        cls.vpc_info = None
        cls.eip_allo_id = None
        cls.public_ip = None
        cls.eip_allo_id_2 = None
        cls.public_ip_2 = None
        cls.ngw_id_1 = None
        cls.eip_allo_id_3 = None
        cls.public_ip_3 = None
        cls.ngw_id_2 = None

    @classmethod
    def teardown_class(cls):
        super(Test_agent_fw_vpc, cls).teardown_class()

    def setup_method(self, method):
        super(Test_agent_fw_vpc, self).setup_method(method)
        self.vpc_info = None
        self.eip_allo_id = None
        self.public_ip = None
        self.eip_allo_id_2 = None
        self.public_ip_2 = None
        self.ngw_id_1 = None
        self.eip_allo_id_3 = None
        self.public_ip_3 = None
        self.ngw_id_2 = None
        try:
            self.vpc_info = create_vpc(osc_sdk=self.a1_r1, nb_subnet=4, nb_instance=1, state='running')

            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.vpc_info[SUBNETS][2][SECURITY_GROUP_ID], IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp='10.0.2.0/24')
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.vpc_info[SUBNETS][3][SECURITY_GROUP_ID], IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp='10.0.2.0/24')

            self.a1_r1.fcu.CreateRoute(RouteTableId=self.vpc_info[SUBNETS][1][ROUTE_TABLE_ID], DestinationCidrBlock='0.0.0.0/0',
                                       GatewayId=self.vpc_info[INTERNET_GATEWAY_ID])

            ret = self.a1_r1.fcu.AllocateAddress()
            self.public_ip = ret.response.publicIp
            ret = self.a1_r1.fcu.DescribeAddresses(PublicIp=[ret.response.publicIp])
            self.eip_allo_id = ret.response.addressesSet[0].allocationId
            ret = self.a1_r1.fcu.AssociateAddress(AllocationId=self.eip_allo_id, InstanceId=self.vpc_info[SUBNETS][1][INSTANCE_ID_LIST][0])

            ret = self.a1_r1.fcu.AllocateAddress()
            self.public_ip_2 = ret.response.publicIp
            ret = self.a1_r1.fcu.DescribeAddresses(PublicIp=[ret.response.publicIp])
            self.eip_allo_id_2 = ret.response.addressesSet[0].allocationId
            ret = self.a1_r1.fcu.CreateNatGateway(AllocationId=self.eip_allo_id_2, SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            self.ngw_id_1 = ret.response.natGateway.natGatewayId

            self.a1_r1.fcu.CreateRoute(RouteTableId=self.vpc_info[SUBNETS][2][ROUTE_TABLE_ID], DestinationCidrBlock='0.0.0.0/0',
                                       GatewayId=self.ngw_id_1)

            ret = self.a1_r1.fcu.AllocateAddress()
            self.public_ip_3 = ret.response.publicIp
            ret = self.a1_r1.fcu.DescribeAddresses(PublicIp=[ret.response.publicIp])
            self.eip_allo_id_3 = ret.response.addressesSet[0].allocationId
            ret = self.a1_r1.fcu.CreateNatGateway(AllocationId=self.eip_allo_id_3, SubnetId=self.vpc_info[SUBNETS][1][SUBNET_ID])
            self.ngw_id_2 = ret.response.natGateway.natGatewayId

            self.a1_r1.fcu.CreateRoute(RouteTableId=self.vpc_info[SUBNETS][3][ROUTE_TABLE_ID], DestinationCidrBlock='0.0.0.0/0',
                                       GatewayId=self.ngw_id_2)

        except Exception as error:
            try:
                self.teardown_method(method)
            finally:
                raise error

    def teardown_method(self, method):
        try:
            # import time
            # time.sleep(300)
            if self.ngw_id_2:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=self.ngw_id_2)
            if self.eip_allo_id_3:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.public_ip_3)
            if self.public_ip_3:
                self.a1_r1.fcu.ReleaseAddress(PublicIp=self.public_ip_3)

            if self.ngw_id_1:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=self.ngw_id_1)
            if self.eip_allo_id_2:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.public_ip_2)
            if self.public_ip_2:
                self.a1_r1.fcu.ReleaseAddress(PublicIp=self.public_ip_2)

            if self.eip_allo_id:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.public_ip)
            if self.public_ip:
                self.a1_r1.fcu.ReleaseAddress(PublicIp=self.public_ip)
            if self.vpc_info:
                delete_vpc(self.a1_r1, self.vpc_info)
        finally:
            super(Test_agent_fw_vpc, self).teardown_method(method)

    def check_ngw_ping(self, pub_ip, kp_path, local_addr, dest_addr):
        sshclient = SshTools.check_connection_paramiko(pub_ip, kp_path,
                                                       username=self.a1_r1.config.region.get_info(constants.CENTOS_USER), retry=4, timeout=10)

        # read file and save it on distant machine
        with open(kp_path, 'r') as content_file:
            content = content_file.read()

        cmd = "sudo echo '" + content + "' > " + kp_path
        out, _, _ = SshTools.exec_command_paramiko(sshclient, cmd)
        self.logger.info(out)
        # put file
        #SshTools.transfer_file_sftp(sshclient, kp_path, kp_path)

        sshclient_jhost = SshTools.check_connection_paramiko_nested(sshclient=sshclient,
                                                                    ip_address=pub_ip,
                                                                    ssh_key=kp_path,
                                                                    local_private_addr=local_addr,
                                                                    dest_private_addr=dest_addr,
                                                                    username=self.a1_r1.config.region.get_info(constants.CENTOS_USER),
                                                                    retry=4, timeout=10)
        cmd = "sudo ping " + Configuration.get('ipaddress', 'dns_google') + " -c 1"
        out, status, _ = SshTools.exec_command_paramiko(sshclient_jhost, cmd)
        self.logger.info(out)
        assert not status, "Subnet that is connected to the NAT gateway seems not to be connected to the internet"

    def test_T1924_agent_fw_vpc_restart(self):
        wait_instances_state(self.a1_r1, self.vpc_info[SUBNETS][1][INSTANCE_ID_LIST], state='ready')
        wait_instances_state(self.a1_r1, self.vpc_info[SUBNETS][2][INSTANCE_ID_LIST], state='ready')
        self.check_ngw_ping(pub_ip=self.public_ip, kp_path=self.vpc_info[KEY_PAIR][PATH],
                            local_addr=self.vpc_info[SUBNETS][1][INSTANCE_SET][0]['privateIpAddress'],
                            dest_addr=self.vpc_info[SUBNETS][2][INSTANCE_SET][0]['privateIpAddress'])
        wait_instances_state(self.a1_r1, self.vpc_info[SUBNETS][3][INSTANCE_ID_LIST], state='ready')
        self.check_ngw_ping(pub_ip=self.public_ip, kp_path=self.vpc_info[KEY_PAIR][PATH],
                            local_addr=self.vpc_info[SUBNETS][1][INSTANCE_SET][0]['privateIpAddress'],
                            dest_addr=self.vpc_info[SUBNETS][3][INSTANCE_SET][0]['privateIpAddress'])

        ret = self.a1_r1.intel.netimpl.firewall.get_firewalls(resource=self.vpc_info[VPC_ID])
        inst_id = ret.response.result.master.vm

        ret = self.a1_r1.intel.nic.find(filters={'vm': inst_id})

        inst_ip = None
        for nic in ret.response.result:
            if IPAddress(nic.ips[0].ip) in IPNetwork(self.a1_r1.config.region.get_info(constants.FW_ADMIN_SUBNET)):
                inst_ip = nic.ips[0].ip
        assert inst_ip

        sshclient = SshTools.check_connection_paramiko(inst_ip,
                                                       os.path.expanduser(self.a1_r1.config.region.get_info(constants.FW_KP)),
                                                       username='root')

        SshTools.exec_command_paramiko(sshclient, "service osc-agent restart")

        self.check_ngw_ping(pub_ip=self.public_ip, kp_path=self.vpc_info[KEY_PAIR][PATH],
                            local_addr=self.vpc_info[SUBNETS][1][INSTANCE_SET][0]['privateIpAddress'],
                            dest_addr=self.vpc_info[SUBNETS][2][INSTANCE_SET][0]['privateIpAddress'])
        self.check_ngw_ping(pub_ip=self.public_ip, kp_path=self.vpc_info[KEY_PAIR][PATH],
                            local_addr=self.vpc_info[SUBNETS][1][INSTANCE_SET][0]['privateIpAddress'],
                            dest_addr=self.vpc_info[SUBNETS][3][INSTANCE_SET][0]['privateIpAddress'])
