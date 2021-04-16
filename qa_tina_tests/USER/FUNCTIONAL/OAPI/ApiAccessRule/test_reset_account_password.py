import string

import pytest

from qa_sdk_pub import osc_api
from qa_test_tools import misc
from qa_tina_tests.USER.FUNCTIONAL.OAPI.ApiAccessRule.api_access import ConfName, setup_api_access_rules, ApiAccess, FAIL, PASS
from qa_test_tools.config import config_constants


@pytest.mark.region_admin
class Test_reset_account_password(ApiAccess):

    def setup_method(self, method):
        ApiAccess.setup_method(self, method)

    def func(self):
        email = self.osc_sdk.config.account.login
        # pid = self.osc_sdk.config.account.account_id
        rettoken = self.osc_sdk.identauth.IdauthPasswordToken.createAccountPasswordToken(
            accountEmail=email,
            account_id=self.a1_r1.config.region.get_info(config_constants.AS_IDAUTH_ID)).response.passwordToken
        password = misc.id_generator(size=20, chars=string.digits + string.ascii_letters)
        self.osc_sdk.icu.ResetAccountPassword(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                                              Password=password, Token=rettoken)


    @setup_api_access_rules(ConfName.NO)
    def test_T5639_ResetAccountPassword_NOIP(self):
        try:
            self.func()
            return [PASS], [PASS], None
        except Exception as error:
            return [FAIL], [PASS], [error]

    @setup_api_access_rules(ConfName.IPOK)
    def test_T5640_ResetAccountPassword_IPOK(self):
        try:
            self.func()
            return [PASS], [PASS], None
        except Exception as error:
            return [FAIL], [PASS], [error]

    @setup_api_access_rules(ConfName.IPKO)
    def test_T5641_ResetAccountPassword_IPKO(self):
        try:
            self.func()
            return [PASS], [PASS], None
        except Exception as error:
            return [FAIL], [PASS], [error]
