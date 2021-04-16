import string

import pytest

from qa_sdk_pub import osc_api
from qa_test_tools import misc
from qa_tina_tests.USER.FUNCTIONAL.OAPI.ApiAccessRule.api_access import ConfName, setup_api_access_rules, ApiAccess, FAIL, PASS


@pytest.mark.region_admin
class Test_reset_account_password(ApiAccess):

    def func(self):
        email = self.osc_sdk.config.account.login
        pid = self.osc_sdk.config.account.account_id
        rettoken = self.osc_sdk.identauth.IdauthPasswordToken.createAccountPasswordToken(accountEmail=email, account_id=pid).response.passwordToken
        password = misc.id_generator(size=20, chars=string.digits + string.ascii_letters)
        self.osc_sdk.icu.ResetAccountPassword(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                                              Password=password, Token=rettoken)


    @setup_api_access_rules(ConfName.NO)
    def test_T9999_ak_sk_NO_CONF_EEY(self):
        try:
            self.func()
            return [PASS], [PASS], None
        except Exception as error:
            return [FAIL], [PASS], [error]

    @setup_api_access_rules(ConfName.IPOK)
    def test_T9999_ak_sk_CONF_IPOK_EEY(self):
        try:
            self.func()
            return [PASS], [PASS], None
        except Exception as error:
            return [FAIL], [PASS], [error]

    @setup_api_access_rules(ConfName.IPKO)
    def test_T9999_ak_sk_CONF_IPKO_EEN(self):
        try:
            self.func()
            return [PASS], [PASS], None
        except Exception as error:
            return [FAIL], [FAIL], [error]
