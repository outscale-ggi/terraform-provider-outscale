import pytest

from qa_sdk_pub import osc_api
from qa_tina_tests.USER.FUNCTIONAL.OAPI.ApiAccessRule.api_access import ConfName, setup_api_access_rules, PASS, FAIL, \
    ApiAccess, KNOWN

AK_SK_FAIL_LIST = [FAIL, FAIL, PASS, FAIL, FAIL, FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL]
AK_SK_PASS_LIST = [PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS]
AK_SK_PASS_LIST_WITH_KNOWN = [PASS, KNOWN, PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS]


@pytest.mark.region_admin
class Test_api_access_ak_sk(ApiAccess):
    
###################################################
# ak-sk
###################################################


    @setup_api_access_rules(ConfName.No)
    def test_T4927_ak_sk_NO_CONF_EEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk},
                               [PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS])

    @setup_api_access_rules(ConfName.IpOK)
    def test_T4928_ak_sk_CONF_IPOK_EEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk},
                               AK_SK_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO)
    def test_T4929_ak_sk_CONF_IPKO_EEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk},
                               AK_SK_FAIL_LIST)

    @setup_api_access_rules(ConfName.Ca)
    def test_T4930_ak_sk_CONF_CA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               AK_SK_PASS_LIST_WITH_KNOWN)

    @setup_api_access_rules(ConfName.Ca)
    def test_T4931_ak_sk_CONF_CA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               AK_SK_FAIL_LIST)

    @setup_api_access_rules(ConfName.CaCn)
    def test_T4932_ak_sk_CONF_CACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                                AK_SK_PASS_LIST_WITH_KNOWN)

    @setup_api_access_rules(ConfName.CaCn)
    def test_T4933_ak_sk_CONF_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                                AK_SK_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOKCa)
    def test_T4934_ak_sk_CONF_IPOKCA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               AK_SK_PASS_LIST_WITH_KNOWN)      

    @setup_api_access_rules(ConfName.IpOKCa)
    def test_T4935_ak_sk_CONF_IPOKCA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               AK_SK_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpKOCa)
    def test_T4936_ak_sk_CONF_IPKOCA_YEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               AK_SK_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOKCaCn)
    def test_T4937_ak_sk_CONF_IPOKCACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               AK_SK_PASS_LIST_WITH_KNOWN)

    @setup_api_access_rules(ConfName.IpOKCaCn)
    def test_T4938_ak_sk_CONF_IPOKCACN_NYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               AK_SK_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOKCaCn)
    def test_T4939_ak_sk_CONF_IPOKCACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               AK_SK_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpKOCaCn)
    def test_T4940_ak_sk_CONF_IPKOCACN_YYN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               AK_SK_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOK_IpKO)
    def test_T4941_ak_sk_CONF_IPOK_IPKO_EEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk},
                               AK_SK_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO_IpKO)
    def test_T4942_ak_sk_CONF_IPKO_IPKO_EEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk},
                               AK_SK_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOK_Ca)
    def test_T4943_ak_sk_CONF_IPOK_CA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               AK_SK_PASS_LIST)

    @setup_api_access_rules(ConfName.IpOK_Ca)
    def test_T4944_ak_sk_CONF_IPOK_CA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               AK_SK_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO_Ca)
    def test_T4945_ak_sk_CONF_IPKO_CA_YEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               AK_SK_PASS_LIST_WITH_KNOWN)

    @setup_api_access_rules(ConfName.IpKO_Ca)
    def test_T4946_ak_sk_CONF_IKO_CA_NEN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               AK_SK_FAIL_LIST)

    @setup_api_access_rules(ConfName.IpOK_CaCn)
    def test_T4947_ak_sk_CONF_IPOK_CACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               AK_SK_PASS_LIST)

    @setup_api_access_rules(ConfName.IpOK_CaCn)
    def test_T4948_ak_sk_CONF_IPOK_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               AK_SK_PASS_LIST)

    @setup_api_access_rules(ConfName.IpKO_CaCn)
    def test_T4949_ak_sk_CONF_IPKO_CACN_YYN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               AK_SK_PASS_LIST_WITH_KNOWN)

    @setup_api_access_rules(ConfName.IpKO_CaCn)
    def test_T4950_ak_sk_CONF_IPKO_CACN_YNN(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               AK_SK_FAIL_LIST)

    @setup_api_access_rules(ConfName.Ca_Ca)
    def test_T4951_ak_sk_CONF_CA_CA_YEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               AK_SK_PASS_LIST_WITH_KNOWN)

    @setup_api_access_rules(ConfName.Ca_Ca)
    def test_T4952_ak_sk_CONF_CA_CA_NEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca3cn1[2], self.certfiles_ca3cn1[1]]},
                               AK_SK_FAIL_LIST)

    @setup_api_access_rules(ConfName.Ca_CaCn)
    def test_T4953_ak_sk_CONF_CA_CACN_NYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca2cn1[2], self.certfiles_ca2cn1[1]]},
                               AK_SK_PASS_LIST_WITH_KNOWN)

    @setup_api_access_rules(ConfName.Ca_CaCn)
    def test_T4954_ak_sk_CONF_CA_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               AK_SK_PASS_LIST_WITH_KNOWN)

    @setup_api_access_rules(ConfName.Ca_CaCn)
    def test_T4955_ak_sk_CONF_CA_CACN_NNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca3cn1[2], self.certfiles_ca3cn1[1]]},
                               AK_SK_FAIL_LIST)

    @setup_api_access_rules(ConfName.CaCn_CaCn)
    def test_T4956_ak_sk_CONF_CACN_CACN_YYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn1[2], self.certfiles_ca1cn1[1]]},
                               AK_SK_PASS_LIST_WITH_KNOWN)

    @setup_api_access_rules(ConfName.CaCn_CaCn)
    def test_T4957_ak_sk_CONF_CACN_CACN_YNY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca1cn2[2], self.certfiles_ca1cn2[1]]},
                               AK_SK_FAIL_LIST)

    @setup_api_access_rules(ConfName.CaCn_CaCn)
    def test_T4958_ak_sk_CONF_CACN_CACN_NYY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                osc_api.EXEC_DATA_CERTIFICATE: [self.certfiles_ca3cn1[2], self.certfiles_ca3cn1[1]]},
                               AK_SK_FAIL_LIST)
