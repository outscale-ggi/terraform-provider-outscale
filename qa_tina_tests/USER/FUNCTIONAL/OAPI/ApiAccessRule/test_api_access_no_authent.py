import pytest

from qa_sdk_pub import osc_api
from qa_tina_tests.USER.FUNCTIONAL.OAPI.ApiAccessRule.api_access import ConfName, setup_api_access_rules, PASS, FAIL, ApiAccess


NO_AUTHENT_FAIL_LIST = [FAIL, FAIL, PASS, FAIL, FAIL, FAIL, FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL]
NO_AUTHENT_PASS_LIST = [FAIL, FAIL, PASS, FAIL, FAIL, FAIL, FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL]


@pytest.mark.region_admin
class Test_api_access_no_authent(ApiAccess):

###################################################
# no-authent
###################################################


    @setup_api_access_rules(ConfName.NO)
    def test_T4991_no_authent_NO_CONF_EEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IPOK)
    def test_T4992_no_authent_CONF_IPOK_EEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IPKO)
    def test_T4993_no_authent_CONF_IPKO_EEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.CA)
    def test_T4994_no_authent_CONF_CA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.CA)
    def test_T4995_no_authent_CONF_CA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               [FAIL, FAIL, PASS, FAIL, FAIL, FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL])

    @setup_api_access_rules(ConfName.CACN)
    def test_T4996_no_authent_CONF_CACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                                NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.CACN)
    def test_T4997_no_authent_CONF_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               [FAIL, FAIL, PASS, FAIL, FAIL, FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL])

    @setup_api_access_rules(ConfName.IPOKCA)
    def test_T4998_no_authent_CONF_IPOKCA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IPOKCA)
    def test_T4999_no_authent_CONF_IPOKCA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.IPKOCA)
    def test_T5000_no_authent_CONF_IPKOCA_YEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.IPOKCACN)
    def test_T5001_no_authent_CONF_IPOKCACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IPOKCACN)
    def test_T5002_no_authent_CONF_IPOKCACN_NYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.IPOKCACN)
    def test_T5003_no_authent_CONF_IPOKCACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.IPKOCACN)
    def test_T5004_no_authent_CONF_IPKOCACN_YYN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.IPOK_IPKO)
    def test_T5005_no_authent_CONF_IPOK_IPKO_EEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IPKO_IPKO)
    def test_T5006_no_authent_CONF_IPKO_IPKO_EEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.IPOK_CA)
    def test_T5007_no_authent_CONF_IPOK_CA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IPOK_CA)
    def test_T5008_no_authent_CONF_IPOK_CA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IPKO_CA)
    def test_T5009_no_authent_CONF_IKO_CA_YEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IPKO_CA)
    def test_T5010_no_authent_CONF_IKO_CA_NEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.IPOK_CACN)
    def test_T5011_no_authent_CONF_IPOK_CACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IPOK_CACN)
    def test_T5012_no_authent_CONF_IPOK_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IPKO_CACN)
    def test_T5013_no_authent_CONF_IPKO_CACN_YYN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.IPKO_CACN)
    def test_T5014_no_authent_CONF_IPKO_CACN_YNN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.CA_CA)
    def test_T5015_no_authent_CONF_CA_CA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.CA_CA)
    def test_T5016_no_authent_CONF_CA_CA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca3cn1[2], self.certfiles_ca3cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.CA_CACN)
    def test_T5017_no_authent_CONF_CA_CACN_NYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.CA_CACN)
    def test_T5018_no_authent_CONF_CA_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.CA_CACN)
    def test_T5019_no_authent_CONF_CA_CACN_NNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca3cn1[2], self.certfiles_ca3cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.CACN_CACN)
    def test_T5020_no_authent_CONF_CACN_CACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               NO_AUTHENT_PASS_LIST)

    @setup_api_access_rules(ConfName.CACN_CACN)
    def test_T5021_no_authent_CONF_CACN_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               NO_AUTHENT_FAIL_LIST)

    @setup_api_access_rules(ConfName.CACN_CACN)
    def test_T5022_no_authent_CONF_CACN_CACN_NYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca3cn1[2], self.certfiles_ca3cn1[1]]},
                               NO_AUTHENT_FAIL_LIST)
