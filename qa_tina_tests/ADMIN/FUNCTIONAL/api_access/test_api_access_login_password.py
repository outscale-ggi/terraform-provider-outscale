from qa_sdk_pub import osc_api
import pytest
from qa_tina_tests.ADMIN.FUNCTIONAL.api_access.api_access import ConfName, setup_api_access_rules, PASS, FAIL, Api_Access

LOGIN_PASSWORD_FAIL_LIST = [FAIL, FAIL, PASS, PASS, FAIL, FAIL, FAIL, FAIL, FAIL, FAIL, FAIL, FAIL]
LOGIN_PASSWORD_PASS_LIST = [FAIL, FAIL, PASS, PASS, FAIL, FAIL, FAIL, FAIL, FAIL, PASS, PASS, FAIL]


@pytest.mark.region_admin
class Test_api_access_login_password(Api_Access):
    
###################################################
# login-password
###################################################


    @setup_api_access_rules(ConfName.No)
    def test_T4959_login_password_NO_CONF_EEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword},
                               [FAIL, FAIL, PASS, PASS, FAIL, FAIL, FAIL, FAIL, FAIL, PASS, PASS, FAIL])

    @setup_api_access_rules(ConfName.IpOK)
    def test_T4960_login_password_CONF_IPOK_EEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword},
                               LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO)
    def test_T4961_login_password_CONF_IPKO_EEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword},
                               LOGIN_PASSWORD_FAIL_LIST)

    @setup_api_access_rules(ConfName.Ca)
    def test_T4962_login_password_CONF_CA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.Ca)
    def test_T4963_login_password_CONF_CA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               [FAIL, FAIL, PASS, PASS, FAIL, FAIL, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])

    @setup_api_access_rules(ConfName.CaCn)
    def test_T4964_login_password_CONF_CACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                                LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.CaCn)
    def test_T4965_login_password_CONF_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               [FAIL, FAIL, PASS, PASS, FAIL, FAIL, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])

    @setup_api_access_rules(ConfName.IpOKCa)
    def test_T4966_login_password_CONF_IPOKCA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               LOGIN_PASSWORD_PASS_LIST)      

    @setup_api_access_rules(ConfName.IpOKCa)
    def test_T4967_login_password_CONF_IPOKCA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               LOGIN_PASSWORD_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpKOCa)
    def test_T4968_login_password_CONF_IPKOCA_YEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               LOGIN_PASSWORD_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOKCaCn)
    def test_T4969_login_password_CONF_IPOKCACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.IpOKCaCn)
    def test_T4970_login_password_CONF_IPOKCACN_NYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               LOGIN_PASSWORD_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOKCaCn)
    def test_T4971_login_password_CONF_IPOKCACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               LOGIN_PASSWORD_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpKOCaCn)
    def test_T4972_login_password_CONF_IPKOCACN_YYN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               LOGIN_PASSWORD_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOK_IpKO)
    def test_T4973_login_password_CONF_IPOK_IPKO_EEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword},
                               LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO_IpKO)
    def test_T4974_login_password_CONF_IPKO_IPKO_EEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword},
                               LOGIN_PASSWORD_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOK_Ca)
    def test_T4975_login_password_CONF_IPOK_CA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.IpOK_Ca)
    def test_T4976_login_password_CONF_IPOK_CA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO_Ca)
    def test_T4977_login_password_CONF_IKO_CA_YEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO_Ca)
    def test_T4978_login_password_CONF_IKO_CA_NEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               LOGIN_PASSWORD_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOK_CaCn)
    def test_T4979_login_password_CONF_IPOK_CACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.IpOK_CaCn)
    def test_T4980_login_password_CONF_IPOK_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO_CaCn)
    def test_T4981_login_password_CONF_IPKO_CACN_YYN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO_CaCn)
    def test_T4982_login_password_CONF_IPKO_CACN_YNN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               LOGIN_PASSWORD_FAIL_LIST)

    @setup_api_access_rules(ConfName.Ca_Ca)
    def test_T4983_login_password_CONF_CA_CA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.Ca_Ca)
    def test_T4984_login_password_CONF_CA_CA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca3cn1[2], self.certfiles_ca3cn1[1]]},
                               LOGIN_PASSWORD_FAIL_LIST)

    @setup_api_access_rules(ConfName.Ca_CaCn)
    def test_T4985_login_password_CONF_CA_CACN_NYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.Ca_CaCn)
    def test_T4986_login_password_CONF_CA_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.Ca_CaCn)
    def test_T4987_login_password_CONF_CA_CACN_NNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca3cn1[2], self.certfiles_ca3cn1[1]]},
                               LOGIN_PASSWORD_FAIL_LIST)

    @setup_api_access_rules(ConfName.CaCn_CaCn)
    def test_T4988_login_password_CONF_CACN_CACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               LOGIN_PASSWORD_PASS_LIST)

    @setup_api_access_rules(ConfName.CaCn_CaCn)
    def test_T4989_login_password_CONF_CACN_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               LOGIN_PASSWORD_FAIL_LIST)

    @setup_api_access_rules(ConfName.CaCn_CaCn)
    def test_T4990_login_password_CONF_CACN_CACN_NYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca3cn1[2], self.certfiles_ca3cn1[1]]},
                               LOGIN_PASSWORD_FAIL_LIST)
