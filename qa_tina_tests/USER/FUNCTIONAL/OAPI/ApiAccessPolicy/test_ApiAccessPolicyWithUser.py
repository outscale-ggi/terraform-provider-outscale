from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from specs import check_tools
from qa_test_tools.test_base import known_error
from qa_test_tools import misc
from qa_tina_tools.tina.setup_aap import OscTestAAP

# TODO: merge code with Test_ApiAccessPolicy in qa_tina_tools/tina/setup_aap

class Test_ApiAccessPolicyWithUser(OscTestAAP):

    @classmethod
    def setup_class(cls):
        cls.with_user = True
        super(Test_ApiAccessPolicyWithUser, cls).setup_class()


    def test_T5822_user_check_AEL_wihtout_MFA_ak_sk(self):
        errors = {}
        known_errors = {}
        for api_call, params in self.ael_api_calls.items():
            if api_call.startswith('icu'): # IAM authentication is not supported for ICU
                continue
            func = self.user_sdk
            for elt in api_call.split('.'):
                func = getattr(func, elt)
            try:
                if not params:
                    params = {}
                ret = func(**params)
                errors[api_call] = ret.response.ResponseContext.RequestId
            except OscApiException as error:
                if api_call.startswith("api.") or api_call.startswith("oapi."):
                    try:
                        check_tools.check_oapi_error(error, 4)
                    except Exception as err:
                        errors[api_call] = err
                elif api_call.startswith("eim.ListAccessKeys"):
                    try:
                        misc.assert_error(
                            error,
                            401,
                            'AuthFailure',
                            "Outscale was not able to validate the provided access credentials. Invalid login/password or password has expired.")
                    except Exception as err:
                        errors[api_call] = err
                else:
                    try:
                        misc.assert_error(error, 400, 'AccessDeniedException', "User: None is not authorized to perform:#####")
                    except Exception as err:
                        errors[api_call] = err
        # TODO
        #DeleteAccessKey
        #DeleteApiAccessRule
        #DeleteCa
        #icu.DeleteAccessKey

        for api_call, error in errors.items():
            self.logger.warning("%s: %s", api_call, error)
        assert not errors

        if known_errors:
            for api_call, error in known_errors.items():
                self.logger.warning("%s: %s", api_call, error)
            known_error(list(known_errors.values())[0][0], list(known_errors.values())[0][1])

    def test_T5823_user_check_AEL_with_MFA_ak_sk(self):
        errors = {}
        known_errors = {}
        for api_call, params in self.ael_api_calls.items():
            if api_call.startswith('icu'): # IAM authentication is not supported for ICU
                continue
            func = self.user_sdk
            for elt in api_call.split('.'):
                func = getattr(func, elt)
            try:
                if not params:
                    params= {}
                params['exec_data'] = {osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                       osc_api.EXEC_DATA_CERTIFICATE: [self.client_cert[2], self.client_cert[1]]}
                func(**params)
                if api_call in ['icu.UpdateAccessKey', 'eim.ListAccessKeys', 'icu.CreateAccessKey', 'icu.UpdateAccessKey']:
                    errors[api_call] = "Remove known error"
            except OscApiException as error:
                if api_call == 'icu.UpdateAccessKey' and error.error_code == 'ApiAccessDeniedException':
                    known_errors[api_call] = ('SECSVC-398', "[TrustedEnv] IAM call not in AEL filtered by AAR")
                elif api_call == "eim.ListAccessKeys" and error.status_code == 401 and error.error_code == 'AuthFailure':
                    known_errors[api_call] = ('TINA-6614', "ICU/EIM issues with ApiAccessRules and ApiAccessPolicies")
                elif api_call in ['icu.CreateAccessKey', 'icu.UpdateAccessKey']: # Unable to manage AK/SK ExpirationDate with ICU
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

        if known_errors:
            for api_call, error in known_errors.items():
                self.logger.warning("%s: %s", api_call, error)
            known_error(list(known_errors.values())[0][0], list(known_errors.values())[0][1])

    def test_T5824_user_check_call_with_ak_sk(self):
        errors = {}
        known_errors = {}
        for api_call, params in self.aksk_api_calls.items():
            if api_call.startswith('icu') or api_call.startswith('oos'): # IAM authentication is not supported for ICU / Users not synchronized on oos
                continue
            func = self.user_sdk
            for elt in api_call.split('.'):
                func = getattr(func, elt)
            try:
                if not params:
                    params= {}
                func(**params)
                if api_call == "eim.ListUsers":
                    errors[api_call] = "Remove known error"
            except OscApiException as error:
                if api_call == "eim.ListUsers" and error.status_code == 401 and error.error_code == 'AuthFailure':
                    known_errors[api_call] = ('TINA-6614', "ICU/EIM issues with ApiAccessRules and ApiAccessPolicies")
                else:
                    errors[api_call] = error

        for api_call, error in errors.items():
            self.logger.warning("%s: %s", api_call, error)
        assert not errors

        if known_errors:
            for api_call, error in known_errors.items():
                self.logger.warning("%s: %s", api_call, error)
            known_error(list(known_errors.values())[0][0], list(known_errors.values())[0][1])

    def test_T5825_user_check_call_without_authent(self):
        errors = {}
        for api_call, params in self.pub_api_calls.items():
            func = self.user_sdk
            for elt in api_call.split('.'):
                func = getattr(func, elt)
            try:
                if not params:
                    params= {}
                params['exec_data'] = {osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty}
                func(**params)
            except OscApiException as error:
                errors[api_call] = error

        for api_call, error in errors.items():
            self.logger.warning("%s: %s", api_call, error)
        assert not errors

    def test_T5826_user_create_infinite_ak_sk(self):
        try:
            self.user_sdk.api.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                                        osc_api.EXEC_DATA_CERTIFICATE: [self.client_cert[2], self.client_cert[1]]},)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_tools.check_oapi_error(error, 4118)

    def test_T5827_user_create_finite_ak_sk(self):
        self.user_sdk.api.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                                    osc_api.EXEC_DATA_CERTIFICATE: [self.client_cert[2], self.client_cert[1]]},
                                          ExpirationDate=self.exp_date)

    def test_T5828_user_update_aar_without_cert(self):
        try:
            self.user_sdk.api.UpdateApiAccessRule(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                                            osc_api.EXEC_DATA_CERTIFICATE: [self.client_cert[2], self.client_cert[1]]},
                                                  ApiAccessRuleId=self.aar_id, Description="AAR fo AAP and TrustedEnv", IpRanges=['0.0.0.0/0'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_tools.check_oapi_error(error, 4118)
