from qa_sdk_pub import osc_api
from qa_test_tools import misc
from qa_test_tools.config import config_constants
from qa_tina_tools.tina.setup_aap import OscTestAAP

class Test_ApiAccessPolicyPasswordAndKeyRecovery(OscTestAAP):

    def test_T6047_password_and_key_recovery(self):
        self.osc_sdk.oapi.SendResetPasswordEmail(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                                                 Email=self.email)
        #self.osc_sdk.icu.SendResetPasswordEmail(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
        #                                        Email=self.email)
        rettoken = self.a1_r1.identauth.IdauthPasswordToken.createAccountPasswordToken(
            accountEmail=self.email,
            account_id=self.a1_r1.config.region.get_info(config_constants.AS_IDAUTH_ID))
        new_password = misc.id_generator(size=20)
        self.osc_sdk.oapi.ResetAccountPassword(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                                               Token=rettoken.response.passwordToken, Password=new_password)
        #self.osc_sdk.icu.ResetAccountPassword(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
        #                                      Token=rettoken.response.passwordToken, Password=new_password)
        self.osc_sdk.config.account.password = new_password
        resp = self.osc_sdk.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                                             osc_api.EXEC_DATA_CERTIFICATE: [self.client_cert[2], self.client_cert[1]]}).response
        assert resp.accessKeys
        resp = self.osc_sdk.oapi.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                                             osc_api.EXEC_DATA_CERTIFICATE: [self.client_cert[2], self.client_cert[1]]},
                                                 ExpirationDate=self.exp_date).response
