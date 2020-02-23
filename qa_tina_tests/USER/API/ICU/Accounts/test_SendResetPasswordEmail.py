from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.test_base import OscTestSuite, known_error
from osc_sdk_pub.osc_api import AuthMethod
from time import sleep
from osc_sdk_pub import osc_api


class Test_SendResetPasswordEmail(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_SendResetPasswordEmail, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_SendResetPasswordEmail, cls).teardown_class()

    def test_T3771_check_throttling(self):
        sleep(30)
        found_error = False
        osc_api.disable_throttling()
        try:
            self.a1_r1.icu.SendResetPasswordEmail(Email=self.a1_r1.config.account.login, max_retry=0)
            for _ in range(3):
                try:
                    self.a1_r1.icu.SendResetPasswordEmail(Email=self.a1_r1.config.account.login, max_retry=0)
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

    def test_T3969_non_authenticated(self):
        email = self.a2_r1.icu.GetAccount().response.Account.Email
        self.a2_r1.icu.SendResetPasswordEmail(auth=AuthMethod.Empty, Email=email)
