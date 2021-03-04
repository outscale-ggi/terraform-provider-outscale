import os
import string
from enum import Enum

from qa_sdk_common.exceptions.osc_exceptions import OscApiException, OscSdkException
from qa_sdk_pub import osc_api
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools import misc
from qa_test_tools.account_tools import create_account, delete_account
from qa_test_tools.config import OscConfig
from qa_test_tools.config import config_constants
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.as_.wait_tools import wait_task_state
from qa_tina_tools.tools.tina import create_tools

# other solution, embed call characteristics in calls, expected result can be computed, instead of being
API_CALLS = [
            'directlink.DescribeLocations',  # with AkSk
            'eim.ListAccessKeys',  # with AkSk
            'icu.ReadPublicCatalog',  # without authent
            'icu.ListAccessKeys',  # with LoginPassword
            'icu.ReadQuotas',  # with AkSk
            'icu.GetAccount',  # with AkSk
            'icu.CreateAccount',  # with AkSk
            'fcu.DescribeRegions',  # without authent
            'fcu.DescribeSecurityGroups',  # with AkSk
            # 'kms.ListKeys',  # with AkSk
            'lbu.DescribeLoadBalancers',  # with AkSk
            'oapi.ReadFlexibleGpuCatalog',  # without authent
            'oapi.ReadAccessKeys',  # with LoginPassword
            'oapi.ReadKeypairs'  # with AkSk
            ]

API_DELETE_CALLS = {'icu.CreateAccount': 'xsub.terminate_account'}


def create_account_params():
    customer_id = misc.id_generator(size=8, chars=string.digits)
    return {'City': 'Saint_Cloud',
            'CompanyName': 'Outscale',
            'Country': 'France',
            'CustomerId': customer_id,
            'Email': 'qa+test_api_access_rule_{}@outscale.com'.format(customer_id),
            'FirstName': 'Test_user',
            'LastName': 'Test_Last_name',
            'Password': misc.id_generator(size=20, chars=string.digits + string.ascii_letters),
            'ZipCode': '92210'}


def delete_account_params(delete_params):
    return {'pid': delete_params.response.Account.AccountPid}


API_CREATE_PARAMS = {'icu.CreateAccount': create_account_params}

API_DELETE_PARAMS = {'icu.CreateAccount': delete_account_params}


IP_COND = 'ips'
CA_COND = 'caCertificates'
CN_COND = 'cns'
DESC = 'description'
WRONG_IPS = ['1.1.1.1/32', '2.2.2.0/24']
WRONG_IPS_BIS = ['3.3.3.3/32', '4.4.4.0/24']


class ConfName(Enum):
    No = 'No'
    IpOK = 'IpOK'
    IpKO = 'IpKO'
    Ca = 'Ca'
    CaCn = 'CaCn'
    IpOKCa = 'IpOKCa'
    IpKOCa = 'IpKOCa'
    IpOKCaCn = 'IpOKCaCn'
    IpKOCaCn = 'IpKOCaCn'
    IpOK_IpKO = 'IpOK_IpKO'
    IpKO_IpKO = 'IpKO_IpKO'
    IpOK_Ca = 'IpOK_Ca'
    IpKO_Ca = 'IpKO_Ca'
    IpOK_CaCn = 'IpOK_CaCn'
    IpKO_CaCn = 'IpKO_CaCn'
    Ca_Ca = 'Ca_Ca'
    Ca_CaCn = 'Ca_CaCn'
    Ca_CaCnTest = 'Ca_CaCn'
    CaCn_CaCn = 'CaCnOK_CaCn'


PASS = 0
FAIL = 1
ERROR = 2
KNOWN = 3
ISSUE_PREFIX = "ISSUE --> "

CLIENT_CERT_CN1 = 'client.qa1'
CLIENT_CERT_CN2 = 'client.qa2'
DEFAULT_ACCESS_RULE = {IP_COND: ['0.0.0.0/0'], DESC: 'default_api_access_rule'}
IP_DESC = 'default_ip_access_rule'


def put_configuration(self, access_rules):
    print('put new conf {}'.format(access_rules))
    osc_sdk = self.osc_sdk

    description = None
    if access_rules:
        description = access_rules[0][DESC]

    has_ip_rule = False
    # verification not necessary but just to be sure
    for access_rule in access_rules:
        if access_rule[DESC] != description and access_rule[DESC] != DEFAULT_ACCESS_RULE[DESC]:
            raise OscTestException('Incorrect configuration, all descriptions should be the same')
        if IP_COND in access_rule:
            has_ip_rule = True

    # add default ip rule to avoid problems
    access_rules.append(DEFAULT_ACCESS_RULE)
    if not description:
        description = access_rules[0][DESC]

    # create new rules
    for access_rule in access_rules:
        if not has_ip_rule:
            access_rule[IP_COND] = ['0.0.0.0/0']
#         osc_sdk.oapi.CreateApiAccessRule(CaIds=access_rule[CA_COND] if CA_COND in access_rule else None,
#                                          Cns=access_rule[CN_COND] if CN_COND in access_rule else None,
#                                          Description=access_rule[DESC],
#                                          IpRanges=access_rule[IP_COND] )
        kwargs = {}
        if CA_COND in access_rule:
            kwargs['CaIds'] = access_rule[CA_COND]
        if CN_COND in access_rule:
            kwargs['Cns'] = access_rule[CN_COND]
        if IP_COND in access_rule:
            kwargs['IpRanges'] = access_rule[IP_COND]
        if DESC in access_rule:
            kwargs['Description'] = access_rule[DESC]
        osc_sdk.oapi.CreateApiAccessRule(**kwargs)
        # osc_sdk.identauth.IdauthAccount.createApiAccessRule(
        #    account_id=osc_sdk.config.region.get_info(config_constants.AS_IDAUTH_ID),
        #    principal= {"accountPid": osc_sdk.config.account.account_id}, accessRule=access_rule)

    # delete older rules
    ret = osc_sdk.oapi.ReadApiAccessRules()
    for rule in ret.response.ApiAccessRules:
        if rule.Description != description:
            osc_sdk.oapi.DeleteApiAccessRule(ApiAccessRuleId=rule.ApiAccessRuleId)
    # ret = osc_sdk.identauth.IdauthAccount.listApiAccessRules()
    # print(ret.response.display())
    # for item in ret.response.items:
    #    if item.description != description:
    #        osc_sdk.identauth.IdauthAccount.deleteApiAccessRule(
    #            account_id=osc_sdk.config.region.get_info(config_constants.AS_IDAUTH_ID),
    #            principal={"accountPid":self.account_pid}, accessRulePid=item.pid)

    osc_sdk.identauth__admin.IdauthAdmin.invalidateCache(account_id=osc_sdk.config.region.get_info(config_constants.AS_IDAUTH_ID))

    try:
        print('new api rules:')
        ret = osc_sdk.oapi.ReadApiAccessRules()
        # ret = osc_sdk.identauth.IdauthAccount.listApiAccessRules()
        print(ret.response.display())
    except Exception:
        print('Could not list rules for conf {}'.format([rule for rule in access_rules if rule[DESC] == description]))


# method creating the rules related to the configuration
# it erases any existing rules (a configuration containing these rules is returned)
def setup_api_access_rules(confkey):

    # get current configuration
    # set new configuration
    # return previous configuration
    def _setup_api_access_rules(func):

        def wrapper(self, *args):
            try:
                put_configuration(self, self.configs[confkey])
                actual, expected, errors = func(self, *args)
                issue_names = []
                unexpected = False
                if actual:
                    for i, val in enumerate(actual):
                        if actual[i] != expected[i]:
                            if expected[i] == KNOWN:
                                if isinstance(val, str) and val.startswith(ISSUE_PREFIX):
                                    issue_names.append(val[len(ISSUE_PREFIX):])
                                else:
                                    unexpected = True
                            else:
                                unexpected = True
                    if unexpected:
                        print('actual   results for conf {} -> {}'.format(confkey, actual))
                        print('expected results for conf {} -> {}'.format(confkey, expected))
                        for i, val in enumerate(API_CALLS):
                            print('{} -> {}'.format(val, errors[i]))
                        raise OscTestException('Unexpected result')
                    if issue_names:
                        known_error(' '.join(set(issue_names)), 'Expected known error(s)')
            finally:
                ret = self.a1_r1.identauth.IdauthAccountAdmin.applyDefaultApiAccessRulesAsync(
                    account_id=self.a1_r1.config.region.get_info(config_constants.AS_IDAUTH_ID),
                    accountPids=[self.account_pid])
                try:
                    wait_task_state(osc_sdk=self.a1_r1, state='COMPLETED', task_handle=ret.response.handle)
                except:
                    raise OscTestException('Could not reset api rules in time.')
                self.a1_r1.identauth__admin.IdauthAdmin.invalidateCache(
                    account_id=self.a1_r1.config.region.get_info(config_constants.AS_IDAUTH_ID))

        return wrapper

    return _setup_api_access_rules


class ApiAccess(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.account_pid = None
        cls.tmp_file_paths = []
        super(ApiAccess, cls).setup_class()
        try:
            # create certificates
#             for path in TMP_FILE_LOCATIONS:
#                 if os.path.exists(path):
#                     os.system("rm -rf {}".format(path))
#                 os.mkdir(path)

            cls.ca1files = create_tools.create_caCertificate_file(root='.', cakey='ca1.key', cacrt='ca1.crt',
                                                                  casubject='"/C=FR/ST=Paris/L=Paris/O=outscale/OU=QA/CN=outscale1.com"')
            cls.tmp_file_paths.extend(cls.ca1files)
            cls.ca2files = create_tools.create_caCertificate_file(root='.', cakey='ca2.key', cacrt='ca2.crt',
                                                                  casubject='"/C=FR/ST=Paris/L=Paris/O=outscale/OU=QA/CN=outscale2.com"')
            cls.tmp_file_paths.extend(cls.ca2files)
            cls.ca3files = create_tools.create_caCertificate_file(root='.', cakey='ca3.key', cacrt='ca3.crt',
                                                                  casubject='"/C=FR/ST=Paris/L=Paris/O=outscale/OU=QA/CN=outscale3.com"')
            cls.tmp_file_paths.extend(cls.ca3files)

            cls.certfiles_ca1cn1 = create_tools.create_clientCertificate_files(
                cls.ca1files[0], cls.ca1files[1],
                root='.', clientkey='ca1cn1.key', clientcsr='ca1cn1.csr', clientcrt='ca1cn1.crt',
                clientsubject='/C=FR/ST=Paris/L=Paris/O=outscale/OU=QA/CN={}'.format(CLIENT_CERT_CN1))
            cls.tmp_file_paths.extend(cls.certfiles_ca1cn1)

            cls.certfiles_ca2cn1 = create_tools.create_clientCertificate_files(
                cls.ca2files[0], cls.ca2files[1],
                root='.', clientkey='ca2cn1.key', clientcsr='ca2cn1.csr', clientcrt='ca2cn1.crt',
                clientsubject='/C=FR/ST=Paris/L=Paris/O=outscale/OU=QA/CN={}'.format(CLIENT_CERT_CN1))
            cls.tmp_file_paths.extend(cls.certfiles_ca2cn1)

            cls.certfiles_ca1cn2 = create_tools.create_clientCertificate_files(
                cls.ca1files[0], cls.ca1files[1],
                root='.', clientkey='ca1cn2.key', clientcsr='ca1cn2.csr', clientcrt='ca1cn2.crt',
                clientsubject='/C=FR/ST=Paris/L=Paris/O=outscale/OU=QA/CN={}'.format(CLIENT_CERT_CN2))
            cls.tmp_file_paths.extend(cls.certfiles_ca1cn2)

            cls.certfiles_ca3cn1 = create_tools.create_clientCertificate_files(
                cls.ca3files[0], cls.ca3files[1],
                root='.', clientkey='ca3cn1.key', clientcsr='ca3cn1.csr', clientcrt='ca3cn1.crt',
                clientsubject='/C=FR/ST=Paris/L=Paris/O=outscale/OU=QA/CN={}'.format(CLIENT_CERT_CN1))
            cls.tmp_file_paths.extend(cls.certfiles_ca3cn1)

            email = 'qa+{}@outscale.com'.format(misc.id_generator(prefix='api_access').lower())
            password = misc.id_generator(size=20, chars=string.digits + string.ascii_letters)
            account_info = {'city': 'Saint_Cloud', 'company_name': 'Outscale', 'country': 'France',
                            'email_address': email, 'firstname': 'Test_user', 'lastname': 'Test_Last_name',
                            'password': password, 'zipcode': '92210'}
            cls.account_pid = create_account(cls.a1_r1, account_info=account_info)
            keys = cls.a1_r1.intel.accesskey.find_by_user(owner=cls.account_pid).response.result[0]
            config = OscConfig.get_with_keys(az_name=cls.a1_r1.config.region.az_name, ak=keys.name, sk=keys.secret, account_id=cls.account_pid,
                                             login=email, password=password)
            cls.osc_sdk = OscSdk(config=config)

            cls.osc_sdk.identauth.IdauthEntityLimit.putAccountLimits(account_id=config.region.get_info(config_constants.AS_IDAUTH_ID),
                                                                    accountPid=cls.account_pid,
                                                                    limits={'items': [{"article": 'COUNT_ACCOUNT_CREATED_ACCOUNTS', "value": 100}]})

            cls.ca1_pid = cls.osc_sdk.oapi.CreateCa(CaPem=open(cls.ca1files[1]).read(), Description="ca1files").response.Ca.CaId
            cls.ca2_pid = cls.osc_sdk.oapi.CreateCa(CaPem=open(cls.ca2files[1]).read(), Description="ca2files").response.Ca.CaId
            cls.ca3_pid = cls.osc_sdk.oapi.CreateCa(CaPem=open(cls.ca3files[1]).read(), Description="ca3files").response.Ca.CaId

#             ret = cls.a1_r1.identauth.IdauthAccount.uploadCaCertificate(account_id=cls.a1_r1.config.region.get_info(config_constants.AS_IDAUTH_ID),
#                                                                         name="ca1files", description= "ca1files",
#                                                                         principal= { "accountPid": cls.account_pid, "userPath": 'userpath1' },
#                                                                         body= open(cls.ca1files[1]).read())
#             cls.ca1_pid = ret.response.caCertificateMetadata.pid
# 
#             ret = cls.a1_r1.identauth.IdauthAccount.uploadCaCertificate(account_id=cls.a1_r1.config.region.get_info(config_constants.AS_IDAUTH_ID),
#                                                                         name="ca2files", description= "ca2files",
#                                                                         principal= { "accountPid": cls.account_pid, "userPath": 'userpath2' },
#                                                                         body= open(cls.ca2files[1]).read())
#             cls.ca2_pid = ret.response.caCertificateMetadata.pid
# 
#             ret = cls.a1_r1.identauth.IdauthAccount.uploadCaCertificate(account_id=cls.a1_r1.config.region.get_info(config_constants.AS_IDAUTH_ID),
#                                                                         name="ca3files", description= "ca3files",
#                                                                         principal= { "accountPid": cls.account_pid, "userPath": 'userpath3' },
#                                                                         body= open(cls.ca3files[1]).read())
#             cls.ca3_pid = ret.response.caCertificateMetadata.pid

            # osc_sdk.idenauth ...
            # create configurations
            cls.my_ips = ['172.19.142.254/32']
            cls.configs = {
                ConfName.No: [],
                # IpCriterion
                ConfName.IpOK: [{IP_COND: cls.my_ips, DESC: ConfName.IpOK.value}],
                ConfName.IpKO: [{IP_COND: WRONG_IPS, DESC: ConfName.IpKO.value}],
                # CaCriterion
                ConfName.Ca: [{CA_COND: [cls.ca1_pid], DESC: ConfName.Ca.value}],
                # CaCriterion + CnCriterion
                ConfName.CaCn: [{CA_COND: [cls.ca1_pid], CN_COND: [CLIENT_CERT_CN1], DESC: ConfName.CaCn.value}],
                # IpCriterion + CaCriterion
                ConfName.IpOKCa: [{IP_COND: cls.my_ips, CA_COND: [cls.ca1_pid], DESC: ConfName.IpOKCa.value}],
                ConfName.IpKOCa: [{IP_COND: WRONG_IPS, CA_COND: [cls.ca1_pid], DESC: ConfName.IpKOCa.value}],
                # IpCriterion + CaCriterion + CnCriterion
                ConfName.IpOKCaCn: [{IP_COND: cls.my_ips, CA_COND: [cls.ca1_pid], CN_COND: [CLIENT_CERT_CN1], DESC: ConfName.IpOKCaCn.value}],
                ConfName.IpKOCaCn: [{IP_COND: WRONG_IPS, CA_COND: [cls.ca1_pid], CN_COND: [CLIENT_CERT_CN1], DESC: ConfName.IpKOCaCn.value}],
                
                # IpCritrerion1 , IpCriterion2
                ConfName.IpOK_IpKO: [{IP_COND: cls.my_ips, DESC: ConfName.IpOK_IpKO.value}, {IP_COND: WRONG_IPS, DESC: ConfName.IpOK_IpKO.value}],
                ConfName.IpKO_IpKO: [{IP_COND: WRONG_IPS, DESC: ConfName.IpKO_IpKO.value}, {IP_COND: WRONG_IPS_BIS, DESC: ConfName.IpKO_IpKO.value}],
                # IpCriterion, CaCriterion
                ConfName.IpOK_Ca: [{IP_COND: cls.my_ips, DESC: ConfName.IpOK_Ca.value}, {CA_COND: [cls.ca1_pid], DESC: ConfName.IpOK_Ca.value}],
                ConfName.IpKO_Ca: [{IP_COND: WRONG_IPS, DESC: ConfName.IpKO_Ca.value}, {CA_COND: [cls.ca1_pid], DESC: ConfName.IpKO_Ca.value}],
                # IpCriterion, CaCriterion + CnCriterion
                ConfName.IpOK_CaCn: [{IP_COND: cls.my_ips, DESC: ConfName.IpOK_CaCn.value},
                                     {CA_COND: [cls.ca1_pid], CN_COND: [CLIENT_CERT_CN1], DESC: ConfName.IpOK_CaCn.value}],
                ConfName.IpKO_CaCn: [{IP_COND: WRONG_IPS, DESC: ConfName.IpKO_CaCn.value},
                                     {CA_COND: [cls.ca1_pid], CN_COND: [CLIENT_CERT_CN1], DESC: ConfName.IpKO_CaCn.value}],
                # CaCriterion1, CaCrierion2
                ConfName.Ca_Ca: [{CA_COND: [cls.ca1_pid], DESC: ConfName.Ca_Ca.value}, {CA_COND: [cls.ca2_pid], DESC: ConfName.Ca_Ca.value}],
                # caCriterion1, caCriterion2 + CnCriterion
                ConfName.Ca_CaCn: [{CA_COND: [cls.ca1_pid], DESC: ConfName.Ca_CaCn.value},
                                   {CA_COND: [cls.ca2_pid], CN_COND: [CLIENT_CERT_CN1], DESC: ConfName.Ca_CaCn.value}],
                # caCriterion1 + cnCriterion1, caCriterion2 + CnCriterion2
                ConfName.CaCn_CaCn: [{CA_COND: [cls.ca1_pid], CN_COND: [CLIENT_CERT_CN1], DESC: ConfName.CaCn_CaCn.value},
                                     {CA_COND: [cls.ca2_pid], CN_COND: [CLIENT_CERT_CN1], DESC: ConfName.CaCn_CaCn.value}],
                }

        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error
 
    @classmethod
    def teardown_class(cls):
        try:
            for tmp_file_path in cls.tmp_file_paths:
                try:
                    os.remove(tmp_file_path)
                except Exception as error:
                    print('Could not delete file {} = {}'.format(tmp_file_path, error))
            if cls.account_pid:
                delete_account(cls.a1_r1, cls.account_pid)
        finally:
            super(ApiAccess, cls).teardown_class()

    def make_calls(self, exec_data, expected_results):
        # make all calls, store results and verify against expected results
        results = []
        errors = []
        for i, api_call in enumerate(API_CALLS):
            try:
                # if api_call.startswith('icu.') and expected_results[i] == 1 and exec_data[osc_api.EXEC_DATA_AUTHENTICATION] == osc_api.AuthMethod.AkSk:
                #     expected_results[i] = PASS
                if api_call.startswith('oapi.') and exec_data[osc_api.EXEC_DATA_AUTHENTICATION] == osc_api.AuthMethod.LoginPassword:
                    expected_results[i] = KNOWN
                func = self.osc_sdk
                for elt in api_call.split('.'):
                    func = getattr(func, elt)
                    # print('{}'.format(func))
                response = None
                if api_call in API_CREATE_PARAMS:
                    create_params = API_CREATE_PARAMS[api_call]()
                    response = func(exec_data, **create_params)
                else:
                    response = func(exec_data)
                # print(ret.response.display())
                if api_call in API_DELETE_CALLS:
                    api_delete_call = API_DELETE_CALLS[api_call]
                    func = self.osc_sdk
                    for elt in api_delete_call.split('.'):
                        func = getattr(func, elt)
                        # print('{}'.format(func))
                    if api_call in API_DELETE_PARAMS:
                        delete_params = API_DELETE_PARAMS[api_call](response)
                        func(**delete_params)
                    else:
                        func()
                # print(ret.response.display())
                results.append(PASS)
                errors.append(None)
            except OscApiException as error:
                errors.append(error)
                if error.error_code == 'AuthFailure' and error.status_code == 401:
                    results.append(FAIL)
                elif error.error_code == '1' and error.status_code == 401 and error.message == 'AccessDenied':
                    results.append(FAIL)
                elif error.error_code == '4' and error.status_code == 401 and error.message == 'AccessDenied':
                    results.append(FAIL)
                elif error.status_code == 400 and error.error_code == 'IcuClientException' and error.message == 'Field AuthenticationMethod is required':
                    results.append(FAIL)
                elif error.status_code == 400 and error.error_code == 'AccessDeniedException':
                    results.append(FAIL)
                elif error.status_code == 400 and error.error_code == 'AccessDenied':
                    results.append(FAIL)
                elif error.status_code == 400 and error.error_code == 'UnauthorizedOperation':
                    results.append(FAIL)
                elif api_call == 'eim.ListAccessKeys' and error.status_code == 500 and error.error_code == 'InternalError':
                    results.append('{}TINA-6116'.format(ISSUE_PREFIX))
                elif error.status_code == 401 and error.error_code == 'AuthFailure':
                    results.append(FAIL)
                else:
                    results.append(ERROR)
            except OscSdkException as error:
                errors.append(error)
                if 'login/password authentication is not supported.' in error.message:
                    results.append(FAIL)
                elif api_call.startswith('oapi.') and 'Wrong authentication : only AkSk or Empty is supported.' in error.message:
                    results.append('{}GTW-1240'.format(ISSUE_PREFIX))
                else:
                    results.append(ERROR)
            except Exception as error:
                errors.append(error)
                results.append(ERROR)
        # compare results and expected results
        if expected_results:
            try:
                assert len(expected_results) == len(results)
                for i, val in enumerate(results):
                    assert val == expected_results[i]
            except AssertionError:
                return results, expected_results, errors
        return None, None, None
