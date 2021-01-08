# pylint: disable=missing-docstring

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite


NB_VPC = 2


class Test_DescribeVpcs(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeVpcs, cls).setup_class()
        cls.vpc_id_list = []
        try:
            for _ in range(NB_VPC):
                ret = cls.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
                cls.vpc_id_list.append(ret.response.vpc.vpcId)
            ret = cls.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '1_0_0_0_16'))
            cls.vpc_id_list.append(ret.response.vpc.vpcId)
            ret = cls.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[{'Key': 'domain-name', 'Value': ['outscale.qa']}])
            cls.dhcp_id = ret.response.dhcpOptions.dhcpOptionsId
            cls.a1_r1.fcu.AssociateDhcpOptions(DhcpOptionsId=cls.dhcp_id, VpcId=cls.vpc_id_list[0])
            cls.a1_r1.fcu.CreateTags(ResourceId=[cls.vpc_id_list[0]], Tag=[{'Key': 'toto', 'Value': 'tata'}])
            cls.a1_r1.fcu.CreateTags(ResourceId=[cls.vpc_id_list[1]], Tag=[{'Key': 'tata', 'Value': 'toto'}])
            cls.a1_r1.fcu.CreateTags(ResourceId=[cls.vpc_id_list[2]], Tag=[{'Key': 'tata', 'Value': 'tutu'}])
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            for vpc_id in cls.vpc_id_list:
                cls.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
        finally:
            super(Test_DescribeVpcs, cls).teardown_class()

    def test_T615_without_param(self):
        ret = self.a1_r1.fcu.DescribeVpcs().response.vpcSet
        assert len(set([Vpc.vpcId for Vpc in ret])) == len(self.vpc_id_list)
        for vpc in ret:
            assert vpc.cidrBlock in [Configuration.get('vpc', '10_0_0_0_16'), Configuration.get('vpc', '1_0_0_0_16')]
            assert vpc.vpcId in self.vpc_id_list

    def test_T616_with_valid_vpc_id(self):
        self.a1_r1.fcu.DescribeVpcs(VpcId=[self.vpc_id_list[0]])

    def test_T617_with_invalid_vpc_id(self):
        try:
            self.a1_r1.fcu.DescribeVpcs(VpcId=['toto'])
            assert False, "call should not have been successful, invalid vpc-id"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "The vpc ID 'toto' does not exist"

    def test_T618_with_valid_filter(self):
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'vpc-id', 'Value': self.vpc_id_list[0]}])
        assert len(ret.response.vpcSet) == 1
        self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'state', 'Value': ['pending', 'available']}])
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'cidr', 'Value': Configuration.get('vpc', '10_0_0_0_16')}])
        assert len(ret.response.vpcSet) == 2
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'cidr-block', 'Value': Configuration.get('vpc', '10_0_0_0_16')}])
        assert len(ret.response.vpcSet) == 2
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'cidrBlock', 'Value': Configuration.get('vpc', '10_0_0_0_16')}])
        assert len(ret.response.vpcSet) == 2
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'dhcp-options-id', 'Value': self.dhcp_id}])
        assert len(ret.response.vpcSet) == 1
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'is-default', 'Value': 'false'}])
        assert len(ret.response.vpcSet) == 3
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'isDefault', 'Value': 'false'}])
        assert len(ret.response.vpcSet) == 3
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'tag:toto', 'Value': 'tata'}])
        assert len(ret.response.vpcSet) == 1
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'tag-key', 'Value': 'tata'}])
        assert len(ret.response.vpcSet) == 2
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'tag-value', 'Value': 'toto'}])
        assert len(ret.response.vpcSet) == 1
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'tag-value', 'Value': 'tata'}])
        assert len(ret.response.vpcSet) == 1

    def test_T619_with_invalid_filter(self):
        try:
            self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'toto', 'Value': 'toto'}])
            assert False, "call should not have been successful, invalid filter name"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "The filter 'toto' is invalid"
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'vpc-id', 'Value': 'toto'}])
        assert ret.response.vpcSet is None
        self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'state', 'Value': 'toto'}])
        assert ret.response.vpcSet is None
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'cidr', 'Value': 'toto'}])
        assert ret.response.vpcSet is None
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'cidr-block', 'Value': 'toto'}])
        assert ret.response.vpcSet is None
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'cidrBlock', 'Value': 'toto'}])
        assert ret.response.vpcSet is None
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'dhcp-options-id', 'Value': 'toto'}])
        assert ret.response.vpcSet is None
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'is-default', 'Value': 'toto'}])
        assert ret.response.vpcSet is None
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'isDefault', 'Value': 'toto'}])
        assert ret.response.vpcSet is None
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'tag:toto', 'Value': 'titi'}])
        assert ret.response.vpcSet is None
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'tag-key', 'Value': 'titi'}])
        assert ret.response.vpcSet is None
        ret = self.a1_r1.fcu.DescribeVpcs(Filter=[{'Name': 'tag-value', 'Value': 'titi'}])
        assert ret.response.vpcSet is None

    def test_T620_with_valid_filter_and_vpc_id(self):
        ret = self.a1_r1.fcu.DescribeVpcs(VpcId=[self.vpc_id_list[0]], Filter=[{'Name': 'vpc-id', 'Value': self.vpc_id_list[0]}])
        assert len(ret.response.vpcSet) == 1

    def test_T3341_with_other_account(self):
        ret = self.a2_r1.fcu.DescribeVpcs()
        assert not ret.response.vpcSet

    def test_T3342_with_other_account_with_param(self):
        try:
            self.a2_r1.fcu.DescribeVpcs(VpcId=[self.vpc_id_list[0]])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpcID.NotFound', "The vpc ID '{}' does not exist".format(self.vpc_id_list[0]))

    def test_T3343_with_other_account_with_filter(self):
        ret = self.a2_r1.fcu.DescribeVpcs(Filter=[{'Name': 'vpc-id', 'Value': self.vpc_id_list}])
        assert not ret.response.vpcSet
