from qa_sdk_pub import osc_api
import pytest
from qa_tina_tests.ADMIN.FUNCTIONAL.api_access.api_access import ConfName, setup_api_access_rules, PASS, FAIL, KNOWN, Api_Access

NO_AUTHENT_FAIL_LIST = [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL]
NO_AUTHENT_PASS_LIST = [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL]


@pytest.mark.region_admin
class Test_api_access_no_authent(Api_Access):
    
###################################################
# no-authent
###################################################


    @setup_api_access_rules(ConfName.No)
    def test_T4991_no_authent_NO_CONF_EEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IpOK)
    def test_T4992_no_authent_CONF_IPOK_EEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO)
    def test_T4993_no_authent_CONF_IPKO_EEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.Ca)
    def test_T4994_no_authent_CONF_CA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.Ca)
    def test_T4995_no_authent_CONF_CA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])

    @setup_api_access_rules(ConfName.CaCn)
    def test_T4996_no_authent_CONF_CACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                                NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.CaCn)
    def test_T4997_no_authent_CONF_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])

    @setup_api_access_rules(ConfName.IpOKCa)
    def test_T4998_no_authent_CONF_IPOKCA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)      

    @setup_api_access_rules(ConfName.IpOKCa)
    def test_T4999_no_authent_CONF_IPOKCA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpKOCa)
    def test_T4500_no_authent_CONF_IPKOCA_YEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOKCaCn)
    def test_T4501_no_authent_CONF_IPOKCACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IpOKCaCn)
    def test_T4502_no_authent_CONF_IPOKCACN_NYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOKCaCn)
    def test_T4503_no_authent_CONF_IPOKCACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpKOCaCn)
    def test_T4504_no_authent_CONF_IPKOCACN_YYN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOK_IpKO)
    def test_T4505_no_authent_CONF_IPOK_IPKO_EEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO_IpKO)
    def test_T4506_no_authent_CONF_IPKO_IPKO_EEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOK_Ca)
    def test_T4507_no_authent_CONF_IPOK_CA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IpOK_Ca)
    def test_T4508_no_authent_CONF_IPOK_CA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO_Ca)
    def test_T4509_no_authent_CONF_IKO_CA_YEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO_Ca)
    def test_T4510_no_authent_CONF_IKO_CA_NEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOK_CaCn)
    def test_T4511_no_authent_CONF_IPOK_CACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IpOK_CaCn)
    def test_T4512_no_authent_CONF_IPOK_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO_CaCn)
    def test_T4513_no_authent_CONF_IPKO_CACN_YYN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO_CaCn)
    def test_T4514_no_authent_CONF_IPKO_CACN_YNN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.Ca_Ca)
    def test_T4515_no_authent_CONF_CA_CA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.Ca_Ca)
    def test_T4516_no_authent_CONF_CA_CA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca3cn1[2], self.certfiles_ca3cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.Ca_CaCn)
    def test_T4517_no_authent_CONF_CA_CACN_NYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.Ca_CaCn)
    def test_T4518_no_authent_CONF_CA_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.Ca_CaCn)
    def test_T4519_no_authent_CONF_CA_CACN_NNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca3cn1[2], self.certfiles_ca3cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.CaCn_CaCn)
    def test_T4520_no_authent_CONF_CACN_CACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.CaCn_CaCn)
    def test_T4521_no_authent_CONF_CACN_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.CaCn_CaCn)
    def test_T4522_no_authent_CONF_CACN_CACN_NYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca3cn1[2], self.certfiles_ca3cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)
