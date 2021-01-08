# pylint: disable=missing-docstring

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_subnets
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.create_tools import create_vpc_old
from qa_tina_tools.tools.tina.wait_tools import wait_subnets_state


class Test_DescribeSubnets(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.subnet_id_list = []
        cls.vpc1_id = None
        cls.vpc2_id = None
        super(Test_DescribeSubnets, cls).setup_class()
        try:
            ret = create_vpc_old(cls.a1_r1, Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc1_id = ret.response.vpc.vpcId
            ret = create_vpc_old(cls.a1_r1, Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc2_id = ret.response.vpc.vpcId
            # subnet 1
            ret = cls.a1_r1.fcu.CreateSubnet(VpcId=cls.vpc1_id, CidrBlock=Configuration.get('subnet', '10_0_1_0_24'),
                                             AvailabilityZone=cls.a1_r1.config.region.az_name)
            subnet_id = ret.response.subnet.subnetId
            cls.subnet_id_list.append(subnet_id)
            # subnet 2
            ret = cls.a1_r1.fcu.CreateSubnet(VpcId=cls.vpc1_id, CidrBlock=Configuration.get('subnet', '10_0_2_0_24'),
                                             AvailabilityZone=cls.a1_r1.config.region.az_name)
            subnet_id = ret.response.subnet.subnetId
            cls.subnet_id_list.append(subnet_id)
            # subnet 3
            ret = cls.a1_r1.fcu.CreateSubnet(VpcId=cls.vpc2_id, CidrBlock=Configuration.get('subnet', '10_0_3_0_24'))
            subnet_id = ret.response.subnet.subnetId
            cls.subnet_id_list.append(subnet_id)
            # subnet 4
            ret = cls.a1_r1.fcu.CreateSubnet(VpcId=cls.vpc2_id, CidrBlock=Configuration.get('subnet', '10_0_4_0_24'),
                                             AvailabilityZone=cls.a1_r1.config.region.az_name)
            subnet_id = ret.response.subnet.subnetId
            cls.subnet_id_list.append(subnet_id)
            # subnet 5
            ret = cls.a1_r1.fcu.CreateSubnet(VpcId=cls.vpc2_id, CidrBlock=Configuration.get('subnet', '10_0_5_0_25'),
                                             AvailabilityZone=cls.a1_r1.config.region.az_name)
            subnet_id = ret.response.subnet.subnetId
            cls.subnet_id_list.append(subnet_id)
            wait_subnets_state(cls.a1_r1, subnet_id_list=cls.subnet_id_list, state='available')
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.subnet_id_list:
                cleanup_subnets(cls.a1_r1, subnet_id_list=cls.subnet_id_list)
            if cls.vpc1_id:
                cleanup_vpcs(osc_sdk=cls.a1_r1, vpc_id_list=[cls.vpc1_id])
            if cls.vpc2_id:
                cleanup_vpcs(osc_sdk=cls.a1_r1, vpc_id_list=[cls.vpc2_id])
        finally:
            super(Test_DescribeSubnets, cls).teardown_class()

    def test_T445_dry_run(self):
        try:
            self.a1_r1.fcu.DescribeSubnets(DryRun='true')
        except OscApiException as error:
            assert_error(error, 400, 'DryRunOperation', 'Request would have succeeded, but DryRun flag is set.')

    def test_T443_multi_filter(self):
        filter1 = {"Name": 'cidr', "Value": Configuration.get('subnet', '10_0_1_0_24')}
        filter2 = {"Name": 'state', "Value": 'available'}
        ret = self.a1_r1.fcu.DescribeSubnets(Filter=[filter1, filter2])
        assert len(ret.response.subnetSet) == 1, 'Expected items does not match returned items'
        assert ret.response.subnetSet[0].subnetId == self.subnet_id_list[0]
        assert ret.response.subnetSet[0].cidrBlock == Configuration.get('subnet', '10_0_1_0_24')
        assert ret.response.subnetSet[0].availabilityZone
        assert ret.response.subnetSet[0].availableIpAddressCount

    def test_T437_mono_filter_state(self):
        filter1 = {"Name": 'state', "Value": 'available'}
        ret = self.a1_r1.fcu.DescribeSubnets(Filter=[filter1])
        assert len(ret.response.subnetSet) == 5, 'Expected items does not match returned items'
        for item in ret.response.subnetSet:
            assert item.state == 'available'

    def test_T436_mono_filter_cidr(self):
        filter1 = {"Name": 'cidr', "Value": Configuration.get('subnet', '10_0_1_0_24')}
        ret = self.a1_r1.fcu.DescribeSubnets(Filter=[filter1])
        assert len(ret.response.subnetSet) == 1, 'Expected items does not match returned items'
        assert ret.response.subnetSet[0].subnetId == self.subnet_id_list[0]
        assert ret.response.subnetSet[0].cidrBlock == Configuration.get('subnet', '10_0_1_0_24')
        assert ret.response.subnetSet[0].availabilityZone
        assert ret.response.subnetSet[0].availableIpAddressCount

    def test_T282_mono_filter_availability_zone(self):
        filter1 = {"Name": 'availability-zone', "Value": self.a1_r1.config.region.az_name}
        ret = self.a1_r1.fcu.DescribeSubnets(Filter=[filter1])
        assert len(ret.response.subnetSet) == 5, 'Expected items does not match returned items'
        for sub in ret.response.subnetSet:
            assert sub.availabilityZone == self.a1_r1.config.region.az_name

    def test_T405_mono_filter_vpc_id(self):
        filter1 = {"Name": 'vpc-id', "Value": self.vpc1_id}
        ret = self.a1_r1.fcu.DescribeSubnets(Filter=[filter1])
        assert len(ret.response.subnetSet) == 2, 'Expected items does not match returned items'
        assert self.vpc1_id in (subnet.vpcId for subnet in ret.response.subnetSet)
        assert self.vpc2_id not in (subnet.vpcId for subnet in ret.response.subnetSet)

    def test_T403_mono_filter_subnet_id(self):
        filter1 = {"Name": 'subnet-id', "Value": self.subnet_id_list[0]}
        ret = self.a1_r1.fcu.DescribeSubnets(Filter=[filter1])
        assert len(ret.response.subnetSet) == 1, 'Expected items does not match returned items'
        assert ret.response.subnetSet[0].subnetId == self.subnet_id_list[0]
        assert ret.response.subnetSet[0].cidrBlock == Configuration.get('subnet', '10_0_1_0_24')
        assert ret.response.subnetSet[0].availabilityZone
        assert ret.response.subnetSet[0].availableIpAddressCount

    def test_T401_mono_filter_available_ip_address_count(self):
        filter1 = {"Name": 'available-ip-address-count', "Value": 123}
        ret = self.a1_r1.fcu.DescribeSubnets(Filter=[filter1])
        assert len(ret.response.subnetSet) == 1, 'Expected items does not match returned items'
        assert ret.response.subnetSet[0].subnetId == self.subnet_id_list[4]
        assert ret.response.subnetSet[0].cidrBlock == Configuration.get('subnet', '10_0_5_0_25')
        assert ret.response.subnetSet[0].availabilityZone
        assert ret.response.subnetSet[0].availableIpAddressCount

    def test_T2167_without_param(self):
        ret = self.a1_r1.fcu.DescribeSubnets().response.subnetSet
        assert len(set([subnet.subnetId for subnet in ret])) == len(self.subnet_id_list)
        for subnet in ret:
            assert subnet.mapPublicIpOnLaunch == "false"
            assert subnet.subnetId in self.subnet_id_list

    def test_T3240_with_other_account_with_param(self):
        try:
            self.a2_r1.fcu.DescribeSubnets(SubnetId=self.subnet_id_list[:1])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSubnetID.NotFound', "The subnet ID '{}' does not exist".format(self.subnet_id_list[0]))

    def test_T3241_with_other_account_with_filter(self):
        ret = self.a2_r1.fcu.DescribeSubnets(Filter=[{'Name': 'subnet-id', 'Value': self.subnet_id_list}])
        assert not ret.response.subnetSet

    def test_T3239_with_other_account(self):
        ret = self.a2_r1.fcu.DescribeSubnets()
        assert not ret.response.subnetSet, 'Unexpected non-empty result'
