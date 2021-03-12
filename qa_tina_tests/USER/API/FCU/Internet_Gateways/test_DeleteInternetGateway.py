from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_DeleteInternetGateway(OscTestSuite):

    def test_T3919_with_correct_igw_id(self):
        ret = self.a1_r1.fcu.CreateInternetGateway().response
        self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=ret.internetGateway.internetGatewayId)

    def test_T3920_with_incorrect_igw_id(self):
        ret = self.a1_r1.fcu.CreateInternetGateway().response
        igw_id = ret.internetGateway.internetGatewayId
        try:
            self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=str(igw_id + "test"))
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInternetGatewayID.Malformed', "Invalid ID received: {}test".format(igw_id))
        finally:
            self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=igw_id)

    def test_T3922_not_existing_igw_id(self):
        ret = self.a1_r1.fcu.CreateInternetGateway().response
        igw_id = ret.internetGateway.internetGatewayId
        try:
            self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId="igw-00000000")
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInternetGatewayID.NotFound', "The InternetGatewayId 'igw-00000000' does not exist")
        finally:
            self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=igw_id)

    def test_T3921_without_igw_id(self):
        try:
            self.a1_r1.fcu.DeleteInternetGateway()
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: GatewayID')

    def test_T3945_from_another_account(self):
        delete_result = None
        ret = self.a1_r1.fcu.CreateInternetGateway().response
        igw_id = ret.internetGateway.internetGatewayId
        try:
            delete_result = self.a2_r1.fcu.DeleteInternetGateway(InternetGatewayId=igw_id)
        except OscApiException as error:
            assert_error(error, 400, "InvalidInternetGatewayID.NotFound", "The InternetGatewayId '{}' does not exist".format(igw_id))
        finally:
            if delete_result:
                self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=igw_id)
