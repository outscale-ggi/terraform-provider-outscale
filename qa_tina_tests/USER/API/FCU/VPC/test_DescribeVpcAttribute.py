

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite

NB_VPC = 2


class Test_DescribeVpcAttribute(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeVpcAttribute, cls).setup_class()
        cls.vpc_id_list = []
        try:
            for _ in range(NB_VPC):
                ret = cls.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
                cls.vpc_id_list.append(ret.response.vpc.vpcId)
            ret = cls.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[{'Key': 'domain-name', 'Value': ['outscale.qa']}])
            cls.dhcp_id = ret.response.dhcpOptions.dhcpOptionsId
            cls.a1_r1.fcu.AssociateDhcpOptions(DhcpOptionsId=cls.dhcp_id, VpcId=cls.vpc_id_list[0])
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
            super(Test_DescribeVpcAttribute, cls).teardown_class()

    def test_T3419_with_other_account_with_param(self):
        try:
            self.a2_r1.fcu.DescribeVpcAttribute(Attribute='enableDnsHostnames', VpcId=self.vpc_id_list[0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpcID.NotFound', "The vpc ID '{}' does not exist".format(self.vpc_id_list[0]))

    def test_T3420_without_attribute(self):
        try:
            self.a1_r1.fcu.DescribeVpcAttribute(VpcId=self.vpc_id_list[0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "The request must contain the parameter: Attribute")

    def test_T3421_without_vpcid(self):
        try:
            self.a1_r1.fcu.DescribeVpcAttribute(Attribute='enableDnsHostnames')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidVpcID.NotFound", "The vpc ID 'None' does not exist")
