from qa_sdk_pub import osc_api
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_test_tools import misc

class Test_UpdateApiAccessPolicy(OscTestSuite):

    def test_T5727_login_password(self):
        try:
            ret = self.a1_r1.oapi.UpdateApiAccessPolicy(
                exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword},
                MaxAccessKeyExpirationSeconds=36000000, RequireTrustedEnv=False)
            assert False, 'Remove known error code'
            ret.check_response()
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameter', '3001')
            known_error('GTW-1961', 'Login Password Authentication does not function')
