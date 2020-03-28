import datetime
import pytest
from qa_common_tools.config.configuration import Configuration
from qa_common_tools.config import config_constants as constants
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_keypair
from qa_tina_tools.tools.tina.delete_tools import delete_keypair, delete_subnet
from qa_tina_tools.tina.info_keys import NAME, PATH
from qa_common_tools.ssh import SshTools
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_common_tools.config.region import Feature


class Test_internet_gateway(OscTestSuite):
    """
        check that from a set of regions
        the others set regions are not available
    """

    @classmethod
    def setup_class(cls):
        super(Test_internet_gateway, cls).setup_class()
        cls.vpc_id = None
        cls.subnet1_id = None
        cls.igw_id = None
        cls.kp_info = None
        cls.inst1_id = None
        cls.eip = None
        cls.rtb1 = None
        cls.rt_asso1_id = None
        cls.eip_allo_id = None
        try:
            Instance_Type = cls.a1_r1._config.region.get_info(constants.DEFAULT_INSTANCE_TYPE)
            IP_Ingress = Configuration.get('cidr', 'allips')
            time_now = datetime.datetime.now()
            unique_id = time_now.strftime('%Y%m%d%H%M%S')
            cls.sg_name = 'sg_test_int_conn_IGW_{}'.format(unique_id)
            cls.sg_id = None
            # allocate eip
            cls.eip = cls.a1_r1.fcu.AllocateAddress()
            # get allocationID
            ret = cls.a1_r1.fcu.DescribeAddresses(PublicIp=[cls.eip.response.publicIp])
            cls.eip_allo_id = ret.response.addressesSet[0].allocationId
            # create keypair
            cls.kp_info = create_keypair(cls.a1_r1)
            # create VPC
            vpc = cls.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc_id = vpc.response.vpc.vpcId
            sg_response = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=cls.sg_name, VpcId=cls.vpc_id)
            cls.sg_id = sg_response.response.groupId
            # create route tables1
            ret = cls.a1_r1.fcu.CreateRouteTable(VpcId=cls.vpc_id)
            cls.rtb1 = ret.response.routeTable.routeTableId
            # authorize rules
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=cls.sg_id, IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp=IP_Ingress)
            # create subnet 1
            ret = cls.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_1_0_24'), VpcId=cls.vpc_id)
            cls.subnet1_id = ret.response.subnet.subnetId
            # accociate routetable 1
            ret = cls.a1_r1.fcu.AssociateRouteTable(RouteTableId=cls.rtb1, SubnetId=cls.subnet1_id)
            cls.rt_asso1_id = ret.response.associationId
            # run instance
            inst = cls.a1_r1.fcu.RunInstances(ImageId=cls.a1_r1._config.region.get_info(constants.CENTOS7), MaxCount='1',
                                              MinCount='1',
                                              SecurityGroupId=cls.sg_id, KeyName=cls.kp_info[NAME],
                                              InstanceType=Instance_Type, SubnetId=cls.subnet1_id)
            cls.inst1_id = inst.response.instancesSet[0].instanceId
            # wait instance to become ready
            wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=[cls.inst1_id], state='ready')
            # create internetgateway
            ret = cls.a1_r1.fcu.CreateInternetGateway()
            cls.igw_id = ret.response.internetGateway.internetGatewayId
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst1_id:
                # terminate the instance
                cls.a1_r1.fcu.TerminateInstances(InstanceId=[cls.inst1_id])
                # replace by wait function
                wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=[cls.inst1_id], state='terminated')
            if cls.subnet1_id:
                delete_subnet(cls.a1_r1, cls.subnet1_id)
            if cls.igw_id:
                cls.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=cls.igw_id, VpcId=cls.vpc_id)
                cls.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=cls.igw_id)
            if cls.sg_id:
                cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.sg_id)
            if cls.rtb1:
                cls.a1_r1.fcu.DeleteRouteTable(RouteTableId=cls.rtb1)
            if cls.vpc_id:
                cls.a1_r1.fcu.DeleteVpc(VpcId=cls.vpc_id)
            if cls.kp_info:
                delete_keypair(cls.a1_r1, cls.kp_info)
            if cls.eip:
                cls.a1_r1.fcu.ReleaseAddress(PublicIp=cls.eip.response.publicIp)
        finally:
            super(Test_internet_gateway, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T118_internet_gateway(self):
        cidr = Configuration.get('cidr', 'allips')
        self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_id)
        # add route RTB1
        self.a1_r1.fcu.CreateRoute(DestinationCidrBlock=cidr, GatewayId=self.igw_id, RouteTableId=self.rtb1)
        self.a1_r1.fcu.AssociateAddress(AllocationId=self.eip_allo_id, InstanceId=self.inst1_id)
        sshclient = SshTools.check_connection_paramiko(self.eip.response.publicIp, self.kp_info[PATH],
                                                       username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        if Feature.INTERNET in self.a1_r1.config.region.get_info(constants.FEATURES):
            target_ip = Configuration.get('ipaddress', 'dns_google')
        else:
            target_ip = '.'.join(self.eip.response.publicIp.split('.')[:-1]) + '.254'
        cmd = "ping " + target_ip + " -c 1"
        out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
        self.logger.info(out)
        # check ping google DNS
        assert not status, "Subnet that is connected to the internet gateway {} seems not to be connected to the internet".format(self.igw_id)
