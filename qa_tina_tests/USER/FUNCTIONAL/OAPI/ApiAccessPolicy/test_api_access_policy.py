import datetime
import os
import string
import hashlib
import hmac

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdks import OscSdk
from qa_sdk_pub import osc_api
from qa_test_tools import account_tools, misc
from qa_test_tools.config import OscConfig, config_constants
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina import create_tools

def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def get_signing_key(key, date_stamp, region_name, service_name):
    k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    k_signing = sign(k_service, 'osc4_request')
    return k_signing


class Test_ApiAccessPolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.account_pid = None
        cls.osc_sdk = None
        cls.ca_files = None
        cls.ca_id = None
        cls.client_cert = None
        cls.exp_date = None
        cls.aar_id = None
        cls.ael_api_calls = {}
        super(Test_ApiAccessPolicy, cls).setup_class()
        try:
            # create account
            email = 'qa+{}@outscale.com'.format(misc.id_generator(prefix='test_api_access_policy').lower())
            password = misc.id_generator(size=20, chars=string.digits + string.ascii_letters)
            account_info = {'city': 'Saint_Cloud', 'company_name': 'Outscale', 'country': 'France',
                            'email_address': email, 'firstname': 'Test_user', 'lastname': 'Test_Last_name',
                            'password': password, 'zipcode': '92210'}
            cls.account_pid = account_tools.create_account(cls.a1_r1, account_info=account_info)
            keys = cls.a1_r1.intel.accesskey.find_by_user(owner=cls.account_pid).response.result[0]
            cls.a1_r1.intel.user.update(username=cls.account_pid, fields={'accesskey_limit': 10})
            cls.osc_sdk = OscSdk(config=OscConfig.get_with_keys(az_name=cls.a1_r1.config.region.az_name, ak=keys.name, sk=keys.secret,
                                                                account_id=cls.account_pid, login=email, password=password))

            # update KP
            # TODO: make call with oapi !!!
            cls.exp_date = (datetime.datetime.utcnow() + datetime.timedelta(minutes=60)).strftime("%Y-%m-%dT%H:%M:%S.000+0000")
            cls.osc_sdk.identauth.IdauthAccount.updateAccessKey(accessKeyPid=keys.name, newExpirationDate=cls.exp_date)

            # create/upload CA
            cls.ca_files = create_tools.create_caCertificate_file()
            cls.ca_id = cls.osc_sdk.oapi.CreateCa(CaPem=open(cls.ca_files[1]).read(), Description="ca1files").response.Ca.CaId
            cls.client_cert = create_tools.create_client_certificate_files(cls.ca_files[0], cls.ca_files[1])

            # create AAR
            resp = cls.osc_sdk.oapi.ReadApiAccessRules().response
            cls.logger.debug(resp.display())
            cls.aar_id = cls.osc_sdk.oapi.CreateApiAccessRule(CaIds=[cls.ca_id],
                                                              Description="AAR fo AAP and TrustedEnv").response.ApiAccessRule.ApiAccessRuleId
            # TODO: RM others AAR....
            for rule in resp.ApiAccessRules:
                cls.osc_sdk.oapi.DeleteApiAccessRule(ApiAccessRuleId=rule.ApiAccessRuleId)
            cls.osc_sdk.identauth__admin.IdauthAdmin.invalidateCache(account_id=cls.osc_sdk.config.region.get_info(config_constants.AS_IDAUTH_ID))

            # create AAP
            cls.osc_sdk.oapi.UpdateApiAccessPolicy(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                                              osc_api.EXEC_DATA_CERTIFICATE: [cls.client_cert[2], cls.client_cert[1]]},
                                                   MaxAccessKeyExpirationSeconds=3600, RequireTrustedEnv=True)

            cls.osc_sdk.identauth__admin.IdauthAdmin.invalidateCache(account_id=cls.osc_sdk.config.region.get_info(config_constants.AS_IDAUTH_ID))


            # Print config for debug
            resp = cls.osc_sdk.oapi.ReadApiAccessRules(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                                                  osc_api.EXEC_DATA_CERTIFICATE: [cls.client_cert[2], cls.client_cert[1]]}).response
            cls.logger.debug(resp.display())
            resp = cls.osc_sdk.oapi.ReadApiAccessPolicy(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                                                   osc_api.EXEC_DATA_CERTIFICATE: [cls.client_cert[2], cls.client_cert[1]]}).response
            cls.logger.debug(resp.display())
            resp = cls.a1_r1.configmanager.CmConfigManager.getConfigEntry(domain='IdentAuth', instance='default',
                                                                          key='apiAccessEngineService.trustedEnvExclusionActions').response
            cls.logger.debug(resp.display())
            #IdentAuth
            #apiAccessEngineService.trustedEnvHandlingEnabled
            #apiAccessEngineService.trustedEnvExclusionActions.retentionHours

            cls.ael_api_calls = {
                'api.CreateAccessKey': {'ExpirationDate': cls.exp_date},
                'api.ReadAccessKeys': None,
                'api.ReadSecretAccessKey' : {'AccessKeyId': keys.name},
                'api.UpdateAccessKey': {'AccessKeyId': keys.name, 'State': "ACTIVE"},
                #'api.DeleteAccessKey'
                'api.CreateApiAccessRule': {'CaIds': [cls.ca_id],
                                            'Description': "New AAR"},
                'api.ReadApiAccessRules': None,
                'api.UpdateApiAccessRule': {'ApiAccessRuleId': cls.aar_id, 'Description': "AAR fo AAP and TrustedEnv", 'CaIds': [cls.ca_id]},
                #'api.DeleteApiAccessRule'
                'api.ReadApiAccessPolicy': None,
                'api.UpdateApiAccessPolicy': {'MaxAccessKeyExpirationSeconds': 3600, 'RequireTrustedEnv': True},
                'api.CreateCa': {'CaPem': open(cls.ca_files[1]).read(), 'Description': "ca1files new"},
                'api.ReadCas': None,
                'api.UpdateCa': {'CaId': cls.ca_id, 'Description': "ca1files"},
                #'api.DeleteCa'
                'icu.CreateAccessKey': None,
                'icu.GetAccessKey': {'AccessKeyId': keys.name},
                'icu.ListAccessKeys': None,
                'icu.UpdateAccessKey': {'AccessKeyId': keys.name, 'Status': "ACTIVE"},
                #'icu.DeleteAccessKey'
            }

        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.client_cert:
                for tmp_file in cls.client_cert:
                    os.remove(tmp_file)
            # if cls.ca_pid: delete CA...
            if cls.ca_files:
                for tmp_file in cls.ca_files:
                    os.remove(tmp_file)
            if cls.account_pid:
                account_tools.delete_account(cls.a1_r1, cls.account_pid)
        finally:
            super(Test_ApiAccessPolicy, cls).teardown_class()


    def test_T0000_as_authent(self):
        ret = self.osc_sdk.api.CreateAccessKey(ExpirationDate=self.exp_date)
        self.logger.debug(ret.response.display())

        info = self.osc_sdk.api.CreateAccessKey(exec_data={osc_api.EXEC_DATA_DRY_RUN: True},
                                                ExpirationDate=self.exp_date)
        #self.logger.debug(info)
        authorization = info['headers']['Authorization']
        cred = authorization.split(' ')[1].split('=')[1].split('/')[0]
        date = authorization.split(' ')[1].split('/')[1]
        reg_name = authorization.split(' ')[1].split('/')[2]
        service = authorization.split(' ')[1].split('/')[3]
        signature = authorization.split(' ')[3].split('=')[1]
        body = "{}\n{}\n{}\n{}".format(
            authorization.split(' ')[0],
            info['headers']['X-Osc-Date'],
            '/'.join(authorization.split(' ')[1].split('/')[1:])[:-1],
            hashlib.sha256(info['canonical_request'].encode('utf-8')).hexdigest()
            )
        ret = self.a1_r1.identauth.IdauthAuthentication.authenticate(
            credentials=cred,
            signature=signature,
            credentialsType="ACCESS_KEY",
            signatureMethod="OSC_V4",
            body=body,
            signatureTokens=[
                {'value': date, 'key': 'Date'},
                {'value': reg_name, 'key': 'Region'},
                {'value': service, 'key': 'Service'},
            ],
            conditionParams=[{'value': misc.get_nat_ips(self.osc_sdk.config.region)[0].split('/')[0], 'key': {'vendor': 'idauth', 'id': 'SourceIp'}}],
        )
        self.logger.debug(ret.response.display())

    def test_T0000_check_AEL_wihtout_MFA(self):
        errors = {}
        for api_call, params in self.ael_api_calls.items():
            func = self.osc_sdk
            for elt in api_call.split('.'):
                func = getattr(func, elt)
            try:
                if params:
                    ret = func(**params)
                else:
                    ret = func()
                #self.logger.debug(ret.response.display())
                errors[api_call] = ret.response.ResponseContext.RequestId
            except OscApiException as error:
                if api_call.startswith("api."):
                    try:
                        misc.assert_oapi_yml(error, 4)
                    except Exception as err:
                        errors[api_call] = err
                else:
                    misc.assert_error(error, 400, 'AccessDeniedException', None)
        # TODO
        #DeleteAccessKey
        #DeleteApiAccessRule
        #DeleteCa
        #icu.DeleteAccessKey

        for api_call, error in errors.items():
            self.logger.warning("%s: %s", api_call, error)
        assert not errors

    def test_T0000_check_AEL_with_MFA(self):
        errors = {}
        for api_call, params in self.ael_api_calls.items():
            func = self.osc_sdk
            for elt in api_call.split('.'):
                func = getattr(func, elt)
            try:
                if not params:
                    params= {}
                params['exec_data'] = {osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                       osc_api.EXEC_DATA_CERTIFICATE: [self.client_cert[2], self.client_cert[1]]}
                func(**params)
                #self.logger.debug(ret.response.display())
            except OscApiException as error:
                if api_call in ['icu.CreateAccessKey', 'icu.UpdateAccessKey']: # Unable to manage AK/SK ExpirationDate with ICU
                    try:
                        misc.assert_error(error, 400, 'InvalidParameterValue',
                                          "code=0, message=u'ServiceValidationException', " + \
                                              "data={'detail': u'accessKey.expirationDate: Access key must expire in 3600 second(s) at most'}")
                    except Exception as err:
                        errors[api_call] = err
                else:
                    errors[api_call] = error

        # TODO
        #DeleteAccessKey
        #DeleteApiAccessRule
        #DeleteCa
        #icu.DeleteAccessKey

        for api_call, error in errors.items():
            self.logger.warning("%s: %s", api_call, error)
        assert not errors

    def test_T0000_check_call_with_ak_sk(self):
        pass

    def test_T0000_check_call_with_login_password(self):
        pass

    def test_T0000_check_call_without_authent(self):
        pass

    def test_T0000_create_infinite_ak_sk(self):
        try:
            self.osc_sdk.api.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                                        osc_api.EXEC_DATA_CERTIFICATE: [self.client_cert[2], self.client_cert[1]]},)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_yml(error, 4118)

    def test_T0000_create_finite_ak_sk(self):
        self.osc_sdk.api.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                                    osc_api.EXEC_DATA_CERTIFICATE: [self.client_cert[2], self.client_cert[1]]},
                                          ExpirationDate=self.exp_date)

    def test_T0000_update_aar_without_cert(self):
        try:
            self.osc_sdk.api.UpdateApiAccessRule(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                                            osc_api.EXEC_DATA_CERTIFICATE: [self.client_cert[2], self.client_cert[1]]},
                                                  ApiAccessRuleId=self.aar_id, Description="AAR fo AAP and TrustedEnv", IpRanges=['0.0.0.0/0'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_yml(error, 4118)
