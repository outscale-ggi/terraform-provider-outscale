import base64
import datetime
import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from qa_test_tools.config.configuration import Configuration
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools import user_data_windows
from qa_tina_tools.tina.check_tools import check_data_from_console, check_winrm_access
from qa_tina_tools.tina.info_keys import NAME, PATH
from qa_tina_tools.tools.tina.create_tools import create_keypair
from qa_tina_tools.tools.tina.delete_tools import delete_keypair, delete_subnet
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


# import os
# import winrm
@pytest.mark.region_windows
class Test_create_using_instance(OscTinaTest):
    @classmethod
    def setup_class(cls):
        super(Test_create_using_instance, cls).setup_class()

        time_now = datetime.datetime.now()
        unique_id = time_now.strftime('%Y%m%d%H%M%S')
        cls.sg_name = 'sg_use_create_win_{}'.format(unique_id)
        cls.sg_name_vpc = 'sg_use_create_win_vpc_{}'.format(unique_id)
        ip_ingress = Configuration.get('cidr', 'allips')

        cls.kp_info = None

        cls.sg_id = None
        cls.sg_id1 = None
        cls.subnet1_id = None
        cls.rtb1 = None
        cls.inst_1_id = None
        cls.inst_2_id = None
        cls.inst_1_pub_IP = None
        cls.inst_2_pub_IP = None

        instance_type = 'tinav4.c4r8p1'
        if cls.a1_r1.config.region.name == 'dv-west-1':
            instance_type = 'tinav1.c4r8p1'
        # TODO : change path to get the correct path on the server
        user_data = user_data_windows.write_slmgr_dlv_to_console_output
        # user_data = user_data_windows.windows_startup
        user_data = base64.b64encode(user_data.encode('utf-8')).decode('utf-8')

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
            sg_response = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=cls.sg_name)

            cls.sg_id = sg_response.response.groupId

            # create security group
            sg_response = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description_vpc', GroupName=cls.sg_name_vpc, VpcId=cls.vpc_id)

            # authorize rules
            cls.sg_id1 = sg_response.response.groupId

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

            # authorize rules
            for sgid in [cls.sg_id, cls.sg_id1]:
                cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=sgid, IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp=ip_ingress)
                cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=sgid, IpProtocol='tcp', FromPort=3389, ToPort=3389, CidrIp=ip_ingress)
                cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=sgid, IpProtocol='tcp', FromPort=5985, ToPort=5985, CidrIp=ip_ingress)
                cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=sgid, IpProtocol='tcp', FromPort=5986, ToPort=5986, CidrIp=ip_ingress)

            # create keypair
            cls.kp_info = create_keypair(cls.a1_r1)

            # run instance
            inst_1 = cls.a1_r1.fcu.RunInstances(
                ImageId=cls.a1_r1.config.region.get_info('windows_omi'),
                MaxCount='1',
                MinCount='1',
                SecurityGroupId=cls.sg_id,
                KeyName=cls.kp_info[NAME],
                InstanceType=instance_type,
                UserData=user_data,
            )

            inst_2 = cls.a1_r1.fcu.RunInstances(
                ImageId=cls.a1_r1.config.region.get_info('windows_omi'),
                MaxCount='1',
                MinCount='1',
                SecurityGroupId=cls.sg_id1,
                KeyName=cls.kp_info[NAME],
                UserData=user_data,
                SubnetId=cls.subnet1_id,
                InstanceType=instance_type,
            )

            cls.inst_1_id = inst_1.response.instancesSet[0].instanceId
            cls.inst_2_id = inst_2.response.instancesSet[0].instanceId

        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            # terminate the instance
            cls.a1_r1.fcu.StopInstances(InstanceId=[cls.inst_1_id, cls.inst_2_id], Force=True)
            # replace by wait function
            wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=[cls.inst_1_id, cls.inst_2_id], state='stopped', threshold=60, wait_time=10)

            # terminate the instance
            cls.a1_r1.fcu.TerminateInstances(InstanceId=[cls.inst_1_id, cls.inst_2_id])
            # replace by wait function
            wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=[cls.inst_1_id, cls.inst_2_id], state='terminated', threshold=60, wait_time=10)

            delete_subnet(cls.a1_r1, cls.subnet1_id)

            cls.a1_r1.fcu.DeleteRouteTable(RouteTableId=cls.rtb1)

            cls.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=cls.igw_id, VpcId=cls.vpc_id)

            cls.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=cls.igw_id)

            cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.sg_id)
            cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.sg_id1)

            cls.a1_r1.fcu.DeleteVpc(VpcId=cls.vpc_id)

            cls.a1_r1.fcu.ReleaseAddress(PublicIp=cls.eip.response.publicIp)

            delete_keypair(cls.a1_r1, cls.kp_info)

            ret = cls.a1_r1.fcu.DescribeVolumes()
            if ret.response.volumeSet and len(ret.response.volumeSet) > 1:
                for vol in ret.response.volumeSet:
                    cls.a1_r1.fcu.DeleteVolume(VolumeId=vol.volumeId)
                known_error('OPS-14000', 'Disk(s) are still available')

        finally:
            super(Test_create_using_instance, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T65_create_using_public_instance(self):

        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[self.inst_1_id], state='ready', threshold=150)

        # get public IP
        time.sleep(5)  # this is needed to avoid request exceeded on prod
        describe_res = self.a1_r1.fcu.DescribeInstances(Filter=[{'Name': 'instance-id', 'Value': [self.inst_1_id]}])
        inst_1_pub_ip = describe_res.response.reservationSet[0].instancesSet[0].ipAddress

        passwd_data = self.a1_r1.fcu.GetPasswordData(InstanceId=self.inst_1_id)
        with open(self.kp_info[PATH], "rb") as key_file:
            private_key = serialization.load_pem_private_key(key_file.read(), password=None, backend=None)
            password = private_key.decrypt(base64.b64decode(passwd_data.response.passwordData), padding.PKCS1v15())

        # self.logger.info("ip : {0}".format(inst_1_pub_IP))
        # self.logger.info("Login Administrator / password {0}".format(password))

        check_data_from_console(self.a1_r1, self.inst_1_id)
        check_winrm_access(inst_1_pub_ip, password)

    @pytest.mark.tag_redwire
    def test_T122_create_using_private_instance_VPC(self):

        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[self.inst_2_id], state='ready', threshold=150)

        self.a1_r1.fcu.AssociateAddress(AllocationId=self.eip_allo_id, InstanceId=self.inst_2_id)
        inst_2_pub_ip = self.eip.response.publicIp

        passwd_data = self.a1_r1.fcu.GetPasswordData(InstanceId=self.inst_2_id)
        with open(self.kp_info[PATH], "rb") as key_file:
            private_key = serialization.load_pem_private_key(key_file.read(), password=None, backend=None)
            password = private_key.decrypt(base64.b64decode(passwd_data.response.passwordData), padding.PKCS1v15())

        # self.logger.info("ip : {0}".format(inst_2_pub_IP))
        # self.logger.info("Login Administrator / password {0}".format(password))

        try:
            check_data_from_console(self.a1_r1, self.inst_2_id)
            if self.a1_r1.config.region.name  == 'dv-west-1':
                pytest.fail('Remove known error')
        except AssertionError:
            if self.a1_r1.config.region.name != 'dv-west-1':
                raise
            # else / if DV1: continue...
        check_winrm_access(inst_2_pub_ip, password)

    # def test_LARS(self):
    #    self.check_winrm_access('198.18.19.73', 'Ui6EH5I@Yenp68Z')
