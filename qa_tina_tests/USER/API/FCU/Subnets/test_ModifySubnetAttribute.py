# pylint: disable=missing-docstring
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, delete_instances
from qa_tina_tools.tools.tina.info_keys import VPC_ID, SUBNETS, SUBNET_ID, INSTANCE_SET
from qa_test_tools.misc import assert_error


class Test_ModifySubnetAttribute(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ModifySubnetAttribute, cls).setup_class()
        cls.vpc_info = None
        try:
            cls.vpc_info = create_vpc(cls.a1_r1)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_ModifySubnetAttribute, cls).teardown_class()

    def test_T2153_without_param(self):
        try:
            self.a1_r1.fcu.ModifySubnetAttribute()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Request is missing the following parameter: SubnetId')

    def test_T2154_with_only_subnet(self):
        self.a1_r1.fcu.ModifySubnetAttribute(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
        ret = self.a1_r1.fcu.DescribeSubnets(SubnetId=[self.vpc_info[SUBNETS][0][SUBNET_ID]])
        assert ret.response.subnetSet[0].mapPublicIpOnLaunch == "false"

    def test_T2155_with_invalid_subnet(self):
        try:
            self.a1_r1.fcu.ModifySubnetAttribute(SubnetId='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSubnetID.Malformed', 'Invalid ID received: foo. Expected format: subnet-')
        try:
            self.a1_r1.fcu.ModifySubnetAttribute(SubnetId='subnet-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSubnetID.NotFound', 'The subnet ID \'subnet-12345678\' does not exist')

    def test_T1973_with_map_public_ip_on_launch(self):
        self.a1_r1.fcu.ModifySubnetAttribute(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID], MapPublicIpOnLaunch={'Value': 'true'})
        ret = self.a1_r1.fcu.DescribeSubnets(SubnetId=[self.vpc_info[SUBNETS][0][SUBNET_ID]])
        assert ret.response.subnetSet[0].mapPublicIpOnLaunch == "true"
        inst_info = None
        nic = None
        try:
            # run instance
            inst_info = create_instances(self.a1_r1, state='running', subnet_id=self.vpc_info[SUBNETS][0][SUBNET_ID])
            assert inst_info[INSTANCE_SET][0]['ipAddress']
            # create nic
            nic = self.a1_r1.fcu.CreateNetworkInterface(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID]).response.networkInterface
            assert nic.association.publicIp
            # check describe eip
            try:
                ret = self.a1_r1.fcu.DescribeAddresses(PublicIp=[inst_info[INSTANCE_SET][0]['ipAddress']])
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'InvalidAddress.NotFound', "Address not found: {}".format(inst_info[INSTANCE_SET][0]['ipAddress']))
            try:
                ret = self.a1_r1.fcu.DescribeAddresses(PublicIp=[nic.association.publicIp])
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'InvalidAddress.NotFound', "Address not found: {}".format(nic.association.publicIp))
        finally:
            if nic:
                self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=nic.networkInterfaceId)
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T2156_with_map_public_ip_on_launch_but_without_igw(self):
        vpc_info = None
        inst_info = None
        nic = None
        try:
            vpc_info = create_vpc(self.a1_r1, igw=False)

            self.a1_r1.fcu.ModifySubnetAttribute(SubnetId=vpc_info[SUBNETS][0][SUBNET_ID], MapPublicIpOnLaunch={'Value': 'true'})
            ret = self.a1_r1.fcu.DescribeSubnets(SubnetId=[vpc_info[SUBNETS][0][SUBNET_ID]])
            assert ret.response.subnetSet[0].mapPublicIpOnLaunch == "true"
            # run instance
            try:
                inst_info = create_instances(self.a1_r1, state='running', subnet_id=vpc_info[SUBNETS][0][SUBNET_ID])
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'Gateway.NotAttached', "Network {} is not attached to any internet gateway".format(vpc_info[VPC_ID]))
            # create nic
            try:
                nic = self.a1_r1.fcu.CreateNetworkInterface(SubnetId=vpc_info[SUBNETS][0][SUBNET_ID]).response.networkInterface
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'Gateway.NotAttached', "Network {} is not attached to any internet gateway".format(vpc_info[VPC_ID]))
        finally:
            if nic:
                self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=nic.networkInterfaceId)
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
            if vpc_info:
                delete_vpc(self.a1_r1, vpc_info)

    def test_T2157_with_invalid_map_public_ip_on_launch(self):
        try:
            self.a1_r1.fcu.ModifySubnetAttribute(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID], MapPublicIpOnLaunch={'Value': 'foo'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Invalid value for parameter 'MapPublicIpOnLaunch.Value': 'foo'")
        try:
            self.a1_r1.fcu.ModifySubnetAttribute(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID], MapPublicIpOnLaunch={'foo': 'true'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Unexpected parameter MapPublicIpOnLaunch.foo")
        try:
            self.a1_r1.fcu.ModifySubnetAttribute(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID], MapPublicIpOnLaunch='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Unexpected parameter MapPublicIpOnLaunch")

    def test_T1972_with_assign_ipv6_address_on_creation(self):
        try:
            self.a1_r1.fcu.ModifySubnetAttribute(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID], AssignIpv6AddressOnCreation={'Value': 'true'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', 'AssignIpv6AddressOnCreation is not supported')

    def test_T2158_with_map_public_ip_on_launch_and_assign_ipv6_address_on_creation(self):
        try:
            self.a1_r1.fcu.ModifySubnetAttribute(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID],
                                                 MapPublicIpOnLaunch={'Value': 'true'}, AssignIpv6AddressOnCreation={'Value': 'true'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', 'AssignIpv6AddressOnCreation is not supported')

    # vpc with/without igw
    # vpc with existing instance
    # address not in describe address
    # value available in describe subnet
    # adress quota exceeded ?
