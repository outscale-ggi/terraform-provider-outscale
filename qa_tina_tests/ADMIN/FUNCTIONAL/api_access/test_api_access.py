from qa_test_tools.test_base import OscTestSuite
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api

# other solution, embed call characteristics in calls, expected result can be computed, instead of being 
API_CALLS = ['fcu.DescribeRegions',  # without authent
             'fcu.DescribeSecurityGroups',
             'oapi.ReadFlexibleGpuCatalog',  # without authent
             'oapi.ReadKeypairs'
            ]

IP_COND = 'ipcond'
CERT_COND = 'certcond'

NO_CONF = None
CONF_IP = [{IP_COND: ['1.2.3.4/32']}]
CONF_CERT = [{CERT_COND: 'cert_path'}]
CONF_IPCERT = [{IP_COND: ['1.2.3.4/32'], CERT_COND: 'cert_path'}]
CONF_IP_IP = [{IP_COND: ['1.2.3.4/32']}, {IP_COND: ['2.3.4.5/32']}]
CONF_IP_CERT = [{IP_COND: ['1.2.3.4/32']}, {CERT_COND: 'cert_path'}]
CONF_CERT_CERT = [{CERT_COND: 'cert_path'}, {CERT_COND: 'cert_path'}]
CONF_IPCERT_IP = [{IP_COND: ['1.2.3.4/32'], CERT_COND: 'cert_path'}, {IP_COND: ['2.3.4.5/32']}]
CONF_IPCERT_IP = [{IP_COND: ['1.2.3.4/32'], CERT_COND: 'cert_path'}, {CERT_COND: 'cert_path'}]
CONF_IPCERT_IPCERT = [{IP_COND: ['1.2.3.4/32'], CERT_COND: 'cert_path'}, {IP_COND: ['2.3.4.5/32'], CERT_COND: 'cert_path'}]


PASS = 0
FAIL = 1
ERROR = 2


# method creating the rules related to the configuration
# it erases any existing rules (a configuration containing these rules is returned)
def setup_api_access_rules(conf):
    # get current configuration
    # set new configuration
    # return previous configuration
    def _setup_api_access_rules(f):
        def wrapper(self, *args):
            print('get previous conf')
            print('put new conf {}'.format(conf))
            f(self, *args)
            print('put previous conf')
        return wrapper
    return _setup_api_access_rules


class Test_api_access(OscTestSuite):
    
#     @classmethod
#     def setup_class(cls):
#         super(Test_api_access, cls).setup_class()
# 
#     @classmethod
#     def teardown_class(cls):
#         super(Test_api_access, cls).teardown_class()
# 
#     def setup_method(self, method):
#         OscTestSuite.setup_method(self, method)
# 
#     def teardown_method(self, method):
#         OscTestSuite.teardown_method(self, method)
    
    def make_calls(self, exec_data, expected_results):
        # make all calls, store results and verify against expected results
        results = []
        for api_call in API_CALLS:
            try:
                func = self.a1_r1
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
                else:
                    results.append(ERROR)
            except:
                results.append(ERROR)
        # compare results and expected results
        if expected_results:
            assert len(expected_results) == len(results)
            for i in range(len(results)):
                assert results[i] == expected_results[i]

    @setup_api_access_rules(NO_CONF)
    def test_T000_no_authent_no_conf(self):
        self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                        [PASS, FAIL, PASS, FAIL])

    @setup_api_access_rules(CONF_IP)
    def test_T000_no_authent_conf_ip(self):
        self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                        [PASS, FAIL, PASS, FAIL])

    @setup_api_access_rules(CONF_CERT)
    def test_T000_no_authent_conf_cert(self):
        self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                        [PASS, FAIL, PASS, FAIL])

    @setup_api_access_rules(CONF_IPCERT)
    def test_T000_no_authent_conf_ip_cert(self):
        self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                        [PASS, FAIL, PASS, FAIL])

    @setup_api_access_rules(NO_CONF)
    def test_T000_aksk_no_conf(self):
        self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk},
                        [PASS, FAIL, PASS, FAIL])

    @setup_api_access_rules(NO_CONF)
    def test_T000_logpwd_no_conf(self):
        self.make_calls({osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword},
                        [PASS, FAIL, PASS, FAIL])

