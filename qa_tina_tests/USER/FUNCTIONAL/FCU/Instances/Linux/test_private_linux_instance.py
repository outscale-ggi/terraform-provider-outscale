import pytest

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_tina_tools.tina import check_tools
from qa_tina_tools.tina.info_keys import PATH
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old, delete_subnet
from qa_tina_tests.USER.FUNCTIONAL.FCU.Instances.Linux.linux_instance import Test_linux_instance


class Test_private_linux_instance(Test_linux_instance):

    @classmethod
    def setup_class(cls):
        super(Test_private_linux_instance, cls).setup_class()
        ip_ingress = Configuration.get('cidr', 'allips')
        cls.subnet1_id = None
        cls.rtb1 = None
        cls.vpc_id = None
        cls.rt_asso1_id = None
        cls.igw_id = None
        cls.sg_vpc_id = None
        try:
            # allocate eip
            cls.eip = cls.a1_r1.fcu.AllocateAddress()
            # get allocationID
            ret = cls.a1_r1.fcu.DescribeAddresses(PublicIp=[cls.eip.response.publicIp])
            cls.eip_allo_id = ret.response.addressesSet[0].allocationId
            # create VPC
            vpc = cls.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc_id = vpc.response.vpc.vpcId
            # create security group
            sg_response = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description_vpc', GroupName=cls.sg_name_vpc, VpcId=cls.vpc_id)
            cls.sg_vpc_id = sg_response.response.groupId
            # authorize rules
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=cls.sg_vpc_id, IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp=ip_ingress)
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
            ret = cls.a1_r1.fcu.CreateRoute(DestinationCidrBlock=ip_ingress, GatewayId=cls.igw_id, RouteTableId=cls.rtb1)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.subnet1_id:
                delete_subnet(cls.a1_r1, cls.subnet1_id)
            if cls.rtb1:
                cls.a1_r1.fcu.DeleteRouteTable(RouteTableId=cls.rtb1)
            if cls.igw_id and cls.vpc_id:
                cls.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=cls.igw_id, VpcId=cls.vpc_id)
            if cls.igw_id:
                cls.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=cls.igw_id)
            if cls.sg_vpc_id:
                cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.sg_vpc_id)
            if cls.vpc_id:
                cls.a1_r1.fcu.DeleteVpc(VpcId=cls.vpc_id)
            cls.a1_r1.fcu.ReleaseAddress(PublicIp=cls.eip.response.publicIp)
        finally:
            super(Test_private_linux_instance, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T112_create_using_linux_instance_vpc(self):
        inst_id = None
        try:
            inst_id, inst_public_ip = self.create_instance(subnet=self.subnet1_id, security_group_id=self.sg_vpc_id,
                                                           eip_alloc_id=self.eip_allo_id,public_ip=self.eip.response.publicIp)
            if inst_id:
                sshclient = check_tools.check_ssh_connection(self.a1_r1, inst_id, inst_public_ip, self.kp_info[PATH],
                                                             username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
                # sshclient = SshTools.check_connection_paramiko(inst_public_ip, self.kp_info[PATH],
                # username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
                cmd = 'pwd'
                out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
                self.logger.info(out)
                assert not status, "SSH command was not executed correctly on the remote host"
        finally:
            try:
                if inst_id:
                    delete_instances_old(self.a1_r1, [inst_id])
            except Exception as error:
                self.logger.exception(error)
                raise error
