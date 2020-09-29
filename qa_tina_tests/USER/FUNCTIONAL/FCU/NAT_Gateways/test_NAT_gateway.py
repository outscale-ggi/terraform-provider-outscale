import datetime
import pytest
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.config import config_constants as constants
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_keypair
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old, delete_keypair, delete_subnet
from qa_common_tools.ssh import SshTools
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_tina_tools.tools.tina import info_keys
from qa_test_tools.config.region import Feature


class Test_NAT_gateway(OscTestSuite):
    """
        check that from a set of regions
        the others set regions are not available
    """

    @classmethod
    def setup_class(cls):
        super(Test_NAT_gateway, cls).setup_class()

        cls.vpc_id = None
        cls.subnet1_id = None
        cls.subnet2_id = None
        cls.igw_id = None
        cls.kp_info = None
        cls.inst1_id = None
        cls.inst2_id = None
        cls.eip = None
        cls.eip2 = None
        cls.rtb1 = None
        cls.rtb2 = None
        cls.rt_asso1_id = None
        cls.rt_asso2_id = None
        cls.eip_allo_id = None
        cls.eip2_allo_id = None
        cls.inst1_local_addr = None
        cls.inst2_local_addr = None

        try:

            Instance_Type = cls.a1_r1.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE)

            IP_Ingress = Configuration.get('cidr', 'allips')
            time_now = datetime.datetime.now()
            unique_id = time_now.strftime('%Y%m%d%H%M%S')
            cls.sg_name = 'sg_test_int_conn_NGW_{}'.format(unique_id)
            cls.all_ips = Configuration.get('cidr', 'allips')

            cls.sg_id = None
            # allocate eip
            cls.eip = cls.a1_r1.fcu.AllocateAddress()

            # get allocationID
            ret = cls.a1_r1.fcu.DescribeAddresses(PublicIp=[cls.eip.response.publicIp])
            cls.eip_allo_id = ret.response.addressesSet[0].allocationId

            # allocate eip
            cls.eip2 = cls.a1_r1.fcu.AllocateAddress()

            ret = cls.a1_r1.fcu.DescribeAddresses(PublicIp=[cls.eip2.response.publicIp])
            cls.eip2_allo_id = ret.response.addressesSet[0].allocationId

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

            # create route tables1
            ret = cls.a1_r1.fcu.CreateRouteTable(VpcId=cls.vpc_id)
            cls.rtb2 = ret.response.routeTable.routeTableId

            # authorize rules
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=cls.sg_id, IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp=IP_Ingress)

            # create subnet 1
            ret = cls.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_1_0_24'), VpcId=cls.vpc_id)
            cls.subnet1_id = ret.response.subnet.subnetId

            # create subnet 2
            ret = cls.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_2_0_24'), VpcId=cls.vpc_id)
            cls.subnet2_id = ret.response.subnet.subnetId

            # accociate routetable 1
            ret = cls.a1_r1.fcu.AssociateRouteTable(RouteTableId=cls.rtb1, SubnetId=cls.subnet1_id)
            cls.rt_asso1_id = ret.response.associationId

            # accociate routetable 2
            ret = cls.a1_r1.fcu.AssociateRouteTable(RouteTableId=cls.rtb2, SubnetId=cls.subnet2_id)
            cls.rt_asso2_id = ret.response.associationId

            # create internetgateway
            ret = cls.a1_r1.fcu.CreateInternetGateway()
            cls.igw_id = ret.response.internetGateway.internetGatewayId

            ret = cls.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=cls.igw_id, VpcId=cls.vpc_id)

            # add route RTB1
            cls.a1_r1.fcu.CreateRoute(DestinationCidrBlock=cls.all_ips, GatewayId=cls.igw_id, RouteTableId=cls.rtb1)

            # run instance
            inst = cls.a1_r1.fcu.RunInstances(ImageId=cls.a1_r1.config.region.get_info(constants.CENTOS7), MaxCount='1',
                                              MinCount='1',
                                              SecurityGroupId=cls.sg_id, KeyName=cls.kp_info[info_keys.NAME],
                                              InstanceType=Instance_Type, SubnetId=cls.subnet1_id)

            cls.inst1_id = inst.response.instancesSet[0].instanceId
            cls.inst1_local_addr = inst.response.instancesSet[0].privateIpAddress

            # run instance
            inst = cls.a1_r1.fcu.RunInstances(ImageId=cls.a1_r1.config.region.get_info(constants.CENTOS7), MaxCount='1',
                                              MinCount='1',
                                              SecurityGroupId=cls.sg_id, KeyName=cls.kp_info[info_keys.NAME],
                                              InstanceType=Instance_Type, SubnetId=cls.subnet2_id)

            cls.inst2_id = inst.response.instancesSet[0].instanceId
            cls.inst2_local_addr = inst.response.instancesSet[0].privateIpAddress

            # wait instance to become ready
            wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=[cls.inst1_id, cls.inst2_id], state='ready')

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
                delete_instances_old(cls.a1_r1, [cls.inst1_id])
            if cls.inst2_id:
                delete_instances_old(cls.a1_r1, [cls.inst2_id])

            if cls.subnet1_id:
                delete_subnet(cls.a1_r1, cls.subnet1_id)

            if cls.subnet2_id:
                delete_subnet(cls.a1_r1, cls.subnet2_id)

            if cls.igw_id and cls.vpc_id:
                cls.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=cls.igw_id, VpcId=cls.vpc_id)

            if cls.igw_id:
                cls.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=cls.igw_id)

            if cls.sg_id:
                cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.sg_id)

            if cls.rtb1:
                cls.a1_r1.fcu.DeleteRouteTable(RouteTableId=cls.rtb1)

            if cls.rtb2:
                cls.a1_r1.fcu.DeleteRouteTable(RouteTableId=cls.rtb2)

            if cls.vpc_id:
                cls.a1_r1.fcu.DeleteVpc(VpcId=cls.vpc_id)

            if cls.kp_info:
                delete_keypair(cls.a1_r1, cls.kp_info)

            if cls.eip:
                cls.a1_r1.fcu.ReleaseAddress(PublicIp=cls.eip.response.publicIp)

            if cls.eip2:
                cls.a1_r1.fcu.ReleaseAddress(PublicIp=cls.eip2.response.publicIp)

        finally:
            super(Test_NAT_gateway, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T66_NAT_gateway(self):

        nwg_id = None
        try:

            ret = self.a1_r1.fcu.CreateNatGateway(AllocationId=self.eip2_allo_id, SubnetId=self.subnet1_id)
            nwg_id = ret.response.natGateway.natGatewayId

            # add route RTB2
            self.a1_r1.fcu.CreateRoute(DestinationCidrBlock=self.all_ips, NatGatewayId=nwg_id, RouteTableId=self.rtb2)

            self.a1_r1.fcu.AssociateAddress(AllocationId=self.eip_allo_id, InstanceId=self.inst1_id)

            sshclient = SshTools.check_connection_paramiko(self.eip.response.publicIp, self.kp_info[info_keys.PATH],
                                                           username=self.a1_r1.config.region.get_info(constants.CENTOS_USER), retry=6, timeout=10)
            # read file and save it on distant machine
            with open(self.kp_info[info_keys.PATH], 'r') as content_file:
                content = content_file.read()

            cmd = "sudo echo '" + content + "' > " + self.kp_info[info_keys.PATH]
            out, _, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
            self.logger.info(out)
            # put file
            # SshTools.transfer_file_sftp(sshclient, self.kp_info[PATH], self.kp_info[PATH])

            cmd = "sudo ifconfig"
            out, _, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
            self.logger.info(out)

            sshclient_jhost = SshTools.check_connection_paramiko_nested(sshclient=sshclient,
                                                                        ip_address=self.eip2.response.publicIp,
                                                                        ssh_key=self.kp_info[info_keys.PATH],
                                                                        local_private_addr=self.inst1_local_addr,
                                                                        dest_private_addr=self.inst2_local_addr,
                                                                        username=self.a1_r1.config.region.get_info(constants.CENTOS_USER),
                                                                        retry=4, timeout=10)

            if Feature.INTERNET in self.a1_r1.config.region.get_info(constants.FEATURES):
                target_ip = Configuration.get('ipaddress', 'dns_google')
            else:
                target_ip = '.'.join(self.eip2.response.publicIp.split('.')[:-1]) + '.254'
            cmd = "sudo ping " + target_ip + " -c 1"
            out, status, _ = SshTools.exec_command_paramiko_2(sshclient_jhost, cmd)
            self.logger.info(out)
            assert not status, "Subnet that is connected to the NAT gateway {} seems not to be connected to the internet".format(nwg_id)

        finally:
            if nwg_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=nwg_id)
