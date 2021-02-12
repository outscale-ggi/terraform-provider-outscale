from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_DeleteVpc(OscTestSuite):

    def test_T613_without_param(self):
        try:
            self.a1_r1.fcu.DeleteVpc()
            assert False, "call should not have been successful, missing param"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "Parameter cannot be empty: VpcID"

    def test_T1303_without_param_existing_vpc(self):
        vpc_id = None
        try:
            ret = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            vpc_id = ret.response.vpc.vpcId
            self.a1_r1.fcu.DeleteVpc(VpcId='vpc-12345678')
            assert False, "call should not have been successful, invalid vpc-id"
        except OscApiException as err:
            assert_error(err, 400, 'InvalidVpcID.NotFound', "The vpc ID 'vpc-12345678' does not exist")
        finally:
            if vpc_id:
                self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)

    def test_T273_with_valid_vpc_id(self):
        ret = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
        vpc_id = ret.response.vpc.vpcId
        self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)

    def test_T614_with_invalid_vpc_id(self):
        try:
            self.a1_r1.fcu.DeleteVpc(VpcId='toto')
            assert False, "call should not have been successful, invalid vpc-id"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "Invalid ID received: toto. Expected format: vpc-"

    def test_T733_delete_from_another_account(self):
        try:
            ret = self.a2_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            vpc_id = ret.response.vpc.vpcId
            self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
            assert False, "call should not have been successful, invalid vpc-id"
        except OscApiException as err:
            try:
                self.a2_r1.fcu.DeleteVpc(VpcId=vpc_id)
            except Exception:
                self.logger.info("Could not delete vpc -> " + vpc_id)
            assert err.status_code == 400
            assert err.message == "The vpc ID '%s' does not exist" % vpc_id
