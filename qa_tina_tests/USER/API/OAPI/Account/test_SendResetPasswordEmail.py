from time import sleep
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_sdk_pub import osc_api
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.specs.check_tools import check_oapi_response
from qa_test_tools import misc


class Test_SendResetPasswordEmail(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_SendResetPasswordEmail, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_SendResetPasswordEmail, cls).teardown_class()

    def test_T4766_check_throttling(self):
        sleep(30)
        found_error = False
        osc_api.disable_throttling()
        try:
            self.a1_r1.oapi.SendResetPasswordEmail(Email=self.a1_r1.config.account.login, exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
            for _ in range(3):
                try:
                    self.a1_r1.oapi.SendResetPasswordEmail(Email=self.a1_r1.config.account.login, exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                except OscApiException as error:
                    if error.status_code == 503:
                        assert False, 'Remove known error code'
                        found_error = True
                    else:
                        raise error
            known_error('TINA-5291', 'throttling ....')
            assert found_error, "Throttling did not happen"
        except OscApiException as error:
            raise error
        finally:
            osc_api.enable_throttling()

    def test_T4767_non_authenticated(self):
        email = self.a2_r1.oapi.ReadAccounts().response.Accounts[0].Email
        ret = self.a2_r1.oapi.SendResetPasswordEmail(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty}, Email=email)
        check_oapi_response(ret.response, 'SendResetPasswordEmailResponse')
