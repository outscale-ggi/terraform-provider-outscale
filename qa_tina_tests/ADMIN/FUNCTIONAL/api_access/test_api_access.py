from qa_test_tools.test_base import OscTestSuite
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_test_tools.account_tools import create_account, delete_account
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
import pytest
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_tina_tools.tools.tina.create_tools import create_certificate_files
from qa_test_tools.config import config_constants
import time


# other solution, embed call characteristics in calls, expected result can be computed, instead of being 
API_CALLS = ['directlink.DescribeLocations',  # with AkSk
             'eim.ListAccessKeys',  # with AkSk
             'icu.ReadPublicCatalog',  # without authent
             'icu.ListAccessKeys',  # with LoginPassword
             'icu.ReadQuotas',  # with AkSk
             'fcu.DescribeRegions',  # without authent
             'fcu.DescribeSecurityGroups',  # with AkSk
             'kms.ListKeys',  # with AkSk
             'lbu.DescribeLoadBalancers',  # with AkSk
             'oapi.ReadFlexibleGpuCatalog',  # without authent
             'oapi.ReadAccessKeys',  # with LoginPassword
             'oapi.ReadKeypairs'  # with AkSk
            ]

IP_COND = 'ipcond'
CA_COND = 'cacond'
CN_COND = 'cncond'

# TODO build valid and invalid conf ip depending on ip of the machine running the tests
NO_CONF = None
CONF_IP = [{IP_COND: ['1.2.3.4/32']}]
CONF_CA = [{CA_COND: 'ca_path'}]
CONF_CN = [{CN_COND: 'cn'}]
CONF_IPCA = [{IP_COND: ['1.2.3.4/32'], CA_COND: 'ca_path'}]
CONF_IPCN = [{IP_COND: ['1.2.3.4/32'], CN_COND: 'cn'}]
CONF_CACN = [{CA_COND: 'ca_path', CN_COND: 'cn'}]
CONF_IPCACN = [{IP_COND: ['1.2.3.4/32'], CA_COND: 'ca_path', CN_COND: 'cn'}]
CONF_IP_IP = [{IP_COND: ['1.2.3.4/32']}, {IP_COND: ['2.3.4.5/32']}]
CONF_IP_CA = [{IP_COND: ['1.2.3.4/32']}, {CA_COND: 'ca_path'}]
CONF_IP_CN = [{IP_COND: ['1.2.3.4/32']}, {CN_COND: 'cn'}]
CONF_CA_CA = [{CA_COND: 'ca_path1'}, {CA_COND: 'ca_path2'}]
CONF_CN_CN = [{CN_COND: 'cn1'}, {CN_COND: 'cn2'}]
CONF_CA_CN = [{CA_COND: 'ca_path'}, {CN_COND: 'cn'}]

PASS = 0
FAIL = 1
ERROR = 2

CLIENT_CERT_CN = 'client.qa'


def put_configuration(osc_sdk, config):
    print('put new conf {}'.format(config))
    # delete any existing rule
    # add 


# method creating the rules related to the configuration
# it erases any existing rules (a configuration containing these rules is returned)
def setup_api_access_rules(conf):

    # get current configuration
    # set new configuration
    # return previous configuration
    def _setup_api_access_rules(f):

        def wrapper(self, *args):
            if conf:
                put_configuration(self.a1_r1, conf)
            actual, expected = f(self, *args)
            if actual:
                print('actual   results for conf {} -> {}'.format(conf, actual))
                print('expected results for conf {} -> {}'.format(conf, expected))
                raise OscTestException('Unexpected result')

        return wrapper

    return _setup_api_access_rules

@pytest.mark.region_admin
class Test_api_access(OscTestSuite):
    
    @classmethod
    def setup_class(cls):
        super(Test_api_access, cls).setup_class()
        cls.account_pid = None
        try:
            cls.account_pid = create_account(cls.a1_r1)
            keys = cls.a1_r1.intel.accesskey.find_by_user(owner=cls.account_pid).response.result[0]
            cls.osc_sdk = OscSdk(config=OscConfig.get_with_keys(az_name=cls.a1_r1.config.region.az_name, ak=keys.name, sk=keys.secret, account_id=cls.account_pid))
            # create certificates
            # TODO create certificates root folder if necessary
            cls.certfiles = create_certificate_files(root='/tmp/cert',
                                                casubject='/C=FR/ST=Paris/L=Paris/O=outscale/OU=QA/CN=outscale.qa',
                                                clientsubject='/C=FR/ST=Paris/L=Paris/O=outscale/OU=QA/CN={}'.format(CLIENT_CERT_CN))
            # TODO upload CA on AS (cls.cerfiles[0])
            # osc_sdk.idenauth ...
        except Exception as error:
            try:
                cls.teardown_class()
            except:
                pass
 
    @classmethod
    def teardown_class(cls):
        try:
            # TODO unload CA from AS
            if cls.account_pid:
                delete_account(cls.a1_r1, cls.account_pid)
            # TODO delete certificates root folder
        finally:
            super(Test_api_access, cls).teardown_class()
 
    def setup_method(self, method):
        super(Test_api_access, self).setup_method(method)
        try:
            self.reset_default_rules()
        except Exception as error:
            try:
                self.teardown_method(method)
            except:
                pass
            raise error
     
    def teardown_method(self, method):
        try:
            self.reset_default_rules()
        except Exception as error:
            raise error
        finally:
            super(Test_api_access, self).teardown_method(method)

    def reset_default_rules(self):
        print('reset default rules')
        for _ in range(5):
            try:
                self.a1_r1.identauth.IdauthAccountAdmin.applyDefaultApiAccessRulesAsync(account_id=self.a1_r1.config.region.get_info(config_constants.AS_IDAUTH_ID), accountPids= [self.account_pid])
                return
            except OscApiException as error:
                if error.error_code != 'ServiceTaskConcurrencyException' or error.status_code != 500:
                    raise error
                time.sleep(2)
        raise OscTestException('Could not apply default rules.')

    def make_calls(self, exec_data, expected_results):
        # make all calls, store results and verify against expected results
        results = []
        for api_call in API_CALLS:
            try:
                func = self.osc_sdk
                for elt in api_call.split('.'):
                    func = getattr(func, elt)
                    # print('{}'.format(func))
                ret = func(exec_data)
                # print(ret.response.display())
                results.append(PASS)
            except OscApiException as error:
                if error.error_code == 'AuthFailure' and error.status_code == 401:
                    results.append(FAIL)
                elif error.error_code == '1' and error.status_code == 401 and error.message == 'AccessDenied':
                    results.append(FAIL)
                elif error.status_code == 400 and error.error_code == 'IcuClientException' and error.message == 'Field AuthenticationMethod is required':
                    results.append(FAIL)
                else:
                    results.append(ERROR)
            except Exception as error:
                results.append(ERROR)
        # compare results and expected results
        if expected_results:
            try:
                assert len(expected_results) == len(results)
                for i in range(len(results)):
                    assert results[i] == expected_results[i]
            except AssertionError:
                return results, expected_results
        return None, expected_results

    @setup_api_access_rules(NO_CONF)
    def test_T000_no_authent_NO_CONF_EEY(self):
        return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                               [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])

#     @setup_api_access_rules(CONF_IP)
#     def test_T000_no_authent_CONF_IP_EEY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
#     
#     @setup_api_access_rules(CONF_IP)
#     def test_T000_no_authent_CONF_IP_EEN(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CA)
#     def test_T000_no_authent_CONF_CA_YEY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CA)
#     def test_T000_no_authent_CONF_CA_NEY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CN)
#     def test_T000_no_authent_CONF_CN_EYY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CN)
#     def test_T000_no_authent_CONF_CN_ENY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IPCA)
#     def test_T000_no_authent_CONF_IPCA_YEY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IPCA)
#     def test_T000_no_authent_CONF_IPCA_YEN(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IPCA)
#     def test_T000_no_authent_CONF_IPCA_NEY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IPCN)
#     def test_T000_no_authent_CONF_IPCN_EYY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IPCN)
#     def test_T000_no_authent_CONF_IPCN_EYN(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IPCN)
#     def test_T000_no_authent_CONF_IPCN_ENY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CACN)
#     def test_T000_no_authent_CONF_CACN_YYY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CACN)
#     def test_T000_no_authent_CONF_CACN_YNY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CACN)
#     def test_T000_no_authent_CONF_CACN_NYY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IP_IP)
#     def test_T000_no_authent_CONF_IP_IP_EEY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IP_IP)
#     def test_T000_no_authent_CONF_IP_IP_EEN(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IP_CA)
#     def test_T000_no_authent_CONF_IP_CA_YEY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IP_CA)
#     def test_T000_no_authent_CONF_IP_CA_YEN(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IP_CA)
#     def test_T000_no_authent_CONF_IP_CA_NEY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IP_CA)
#     def test_T000_no_authent_CONF_IP_CA_NEN(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IP_CN)
#     def test_T000_no_authent_CONF_IP_CN_EYY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IP_CN)
#     def test_T000_no_authent_CONF_IP_CN_EYN(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IP_CN)
#     def test_T000_no_authent_CONF_IP_CN_ENY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IP_CN)
#     def test_T000_no_authent_CONF_IP_CN_ENN(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CA_CA)
#     def test_T000_no_authent_CONF_CA_CA_YEY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CA_CA)
#     def test_T000_no_authent_CONF_CA_CA_NEY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CA_CN)
#     def test_T000_no_authent_CONF_CA_CN_YYY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CA_CN)
#     def test_T000_no_authent_CONF_CA_CN_YNY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CA_CN)
#     def test_T000_no_authent_CONF_CA_CN_NYY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CA_CN)
#     def test_T000_no_authent_CONF_CA_CN_NNY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CN_CN)
#     def test_T000_no_authent_CONF_CN_CN_EYY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_CN_CN)
#     def test_T000_no_authent_CONF_CN_CN_ENY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IPCACN)
#     def test_T000_no_authent_CONF_IPCACN_YYY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IPCACN)
#     def test_T000_no_authent_CONF_IPCACN_YYN(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IPCACN)
#     def test_T000_no_authent_CONF_IPCACN_YNY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IPCACN)
#     def test_T000_no_authent_CONF_IPCACN_YEY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IPCACN)
#     def test_T000_no_authent_CONF_IPCACN_NYY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
# 
#     @setup_api_access_rules(CONF_IPCACN)
#     def test_T000_no_authent_CONF_IPCACN_EYY(self):
#         return self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
#                                [FAIL, FAIL, PASS, FAIL, FAIL, PASS, FAIL, FAIL, FAIL, PASS, FAIL, FAIL])
