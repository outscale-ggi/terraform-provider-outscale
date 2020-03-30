from qa_test_tools.config.configuration import Configuration
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import assert_error


class Test_CreateVpc(OscTestSuite):

    def test_T610_without_param(self):
        try:
            self.a1_r1.fcu.CreateVpc()
            assert False, "call should not have been successful, bad number of parameter"
        except OscApiException as err:
            assert_error(err, 400, "MissingParameter", "Parameter cannot be empty: cidrBlock")

    def test_T608_with_invalid_cidr_block(self):
        try:
            self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc_invalid', '158_8_4_21_29'))
            assert False, "call should not have been successful, invalid cidr block"
        except OscApiException as err:
            assert_error(err, 400, "InvalidVpc.Range", "The CIDR '%s' is invalid." % Configuration.get('vpc_invalid', '158_8_4_21_29'))
        try:
            self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc_invalid', '0_0_0_0_17'))
            assert False, "call should not have been successful, invalid cidr block"
        except OscApiException as err:
            assert_error(err, 400, "InvalidVpc.Range", "The CIDR '%s' is invalid." % Configuration.get('vpc_invalid', '0_0_0_0_17'))
        try:
            self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc_invalid', '255_255_255_0_15'))
            assert False, "call should not have been successful, invalid cidr block"
        except OscApiException as err:
            assert_error(err, 400, "InvalidVpc.Range", "The CIDR '%s' is invalid." % Configuration.get('vpc_invalid', '255_255_255_0_15'))
        try:
            self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc_invalid', '10_0_0_0_42'))
            assert False, "call should not have been successful, invalid cidr block"
        except OscApiException as err:
            assert_error(err, 400, "InvalidParameterValue", "Invalid IPv4 network: %s" % Configuration.get('vpc_invalid', '10_0_0_0_42'))
        try:
            self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc_invalid', '255_255_0_256_16'))
            assert False, "call should not have been successful, invalid cidr block"
        except OscApiException as err:
            assert_error(err, 400, "InvalidParameterValue", "Invalid IPv4 network: %s" % Configuration.get('vpc_invalid', '255_255_0_256_16'))
        try:
            self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc_invalid', '105333_0_0_0_16'))
            assert False, "call should not have been successful, invalid cidr block"
        except OscApiException as err:
            assert_error(err, 400, "InvalidParameterValue", "Invalid IPv4 network: %s" % Configuration.get('vpc_invalid', '105333_0_0_0_16'))
        try:
            self.a1_r1.fcu.CreateVpc(CidrBlock='toto')
            assert False, "call should not have been successful, invalid cidr block"
        except OscApiException as err:
            assert_error(err, 400, "InvalidParameterValue", "Invalid IPv4 network: toto")

    def test_T609_with_valid_cidr_block(self):
        ret = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '255_255_255_255_28'))
        vpc_id = ret.response.vpc.vpcId
        self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
        ret = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '1_0_0_0_16'))
        vpc_id = ret.response.vpc.vpcId
        self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
        ret = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
        vpc_id = ret.response.vpc.vpcId
        self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
        ret = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '172_16_0_0_16'))
        vpc_id = ret.response.vpc.vpcId
        self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
        ret = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '192_168_0_0_24'))
        vpc_id = ret.response.vpc.vpcId
        self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)

    def test_T611_with_valid_instance_tenancy(self):
        ret = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'), InstanceTenancy='dedicated')
        vpc_id = ret.response.vpc.vpcId
        self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
        ret = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'), InstanceTenancy='default')
        vpc_id = ret.response.vpc.vpcId
        self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)

    def test_T612_with_invalid_instance_tenancy(self):
        try:
            self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'), InstanceTenancy='toto')
            assert False, "call should not have been successful, invalid instance tenancy"
        except OscApiException as err:
            assert_error(err, 400, "InvalidParameterValue", "Value (toto) for parameter instanceTenancy is invalid.")
