
from qa_test_tools.config import config_constants as constants

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_peering
from qa_tina_tools.tools.tina.info_keys import SUBNETS, INSTANCE_SET, KEY_PAIR, PATH, VPC_ID, PEERING, EIP, ROUTE_TABLE_ID, SECURITY_GROUP_ID
from qa_common_tools.ssh import SshTools
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs


class Test_VPC_Peering(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc1_info = None
        cls.vpc2_info = None
        super(Test_VPC_Peering, cls).setup_class()

        try:
            cls.vpc2_info = create_vpc(cls.a1_r1, nb_instance=1, no_eip=True, cidr_prefix="172.16", igw=False, default_rtb=False, state='running')
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=cls.vpc2_info[SUBNETS][0][SECURITY_GROUP_ID], IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp='10.0.0.0/16')

            cls.vpc1_info = create_vpc(cls.a1_r1, nb_instance=1, cidr_prefix="10.0", default_rtb=False, state='ready')
            cls.vpc1_inst = cls.vpc1_info[SUBNETS][0][INSTANCE_SET][0]
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc1_info:
                cleanup_vpcs(cls.a1_r1, vpc_id_list=[cls.vpc1_info[VPC_ID]], force=True)
            if cls.vpc2_info:
                cleanup_vpcs(cls.a1_r1, vpc_id_list=[cls.vpc2_info[VPC_ID]], force=True)
        finally:
            super(Test_VPC_Peering, cls).teardown_class()

    def test_T2861_valid_vpc_peering(self):
        try:
            peering_info = create_peering(self.a1_r1, state='active', vpc_id=self.vpc1_info[VPC_ID], peer_vpc_id=self.vpc2_info[VPC_ID])
            assert peering_info[PEERING].status.name == 'active'
            self.a1_r1.fcu.CreateRoute(RouteTableId=self.vpc1_info[SUBNETS][0][ROUTE_TABLE_ID], DestinationCidrBlock='172.16.0.0/16',
                                       VpcPeeringConnectionId=peering_info[PEERING].id)
            self.a1_r1.fcu.CreateRoute(RouteTableId=self.vpc2_info[SUBNETS][0][ROUTE_TABLE_ID], DestinationCidrBlock='10.0.0.0/16',
                                       VpcPeeringConnectionId=peering_info[PEERING].id)
            # connect to instance 1 via eip1
            sshclient = SshTools.check_connection_paramiko(self.vpc1_info[SUBNETS][0][EIP]['publicIp'], self.vpc1_info[KEY_PAIR][PATH],
                                                           username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # connect to instance2 via vpc peering
            sshclient_jhost = SshTools.check_connection_paramiko_nested(
                sshclient=sshclient,
                ip_address=self.vpc2_info[SUBNETS][0][INSTANCE_SET][0]['privateIpAddress'],
                ssh_key=self.vpc2_info[KEY_PAIR][PATH],
                local_private_addr=self.vpc1_info[SUBNETS][0][INSTANCE_SET][0]['privateIpAddress'],
                dest_private_addr=self.vpc2_info[SUBNETS][0][INSTANCE_SET][0]['privateIpAddress'],
                username=self.a1_r1.config.region.get_info(constants.CENTOS_USER),
                retry=4, timeout=10)
            cmd = "sudo ifconfig"
            out, _, _ = SshTools.exec_command_paramiko_2(sshclient_jhost, cmd)
            self.logger.info(out)
        finally:
            if peering_info[PEERING].id:
                self.a1_r1.fcu.DeleteVpcPeeringConnection(VpcPeeringConnectionId=peering_info[PEERING].id)
            if self.vpc1_info[SUBNETS][0][EIP]['publicIp']:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc1_info[SUBNETS][0][EIP]['publicIp'])
                self.a1_r1.fcu.ReleaseAddress(PublicIp=self.vpc1_info[SUBNETS][0][EIP]['publicIp'])
