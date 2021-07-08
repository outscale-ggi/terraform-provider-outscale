from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_test_tools.test_base import known_error
from specs import check_tools
from qa_test_tools import misc
from qa_tina_tools.tina.setup_aap import OscTestAAP

class Test_ApiAccessPolicy(OscTestAAP):

    def test_T5784_check_AEL_wihtout_MFA_ak_sk(self):
        errors = {}
        for api_call, params in self.ael_api_calls.items():
            func = self.osc_sdk
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

    def test_T5785_check_AEL_wihtout_MFA_login_mdp(self):
        errors = {}
        for api_call, params in self.ael_api_calls.items():
            if api_call.startswith('eim'): # authent login/mdp not supported
                continue
            func = self.osc_sdk
            for elt in api_call.split('.'):
                func = getattr(func, elt)
            try:
                if not params:
                    params = {}
                params['exec_data'] = {osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword}
                ret = func(**params)
                errors[api_call] = ret.response.ResponseContext.RequestId
            except OscApiException as error:
                if api_call.startswith("api.") or api_call.startswith("oapi."):
                    try:
                        check_tools.check_oapi_error(error, 14)
                    except Exception as err:
                        errors[api_call] = err
                else:
                    try:
                        misc.assert_error(error, 401, 'AuthFailure',
                                          "Outscale was not able to validate the provided access credentials. " + \
                                              "Invalid login/password or password has expired.")
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

    def test_T5786_check_AEL_with_MFA_ak_sk(self):
        errors = {}
        known_errors = {}
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
            except OscApiException as error:
                if api_call == 'eim.ListAccessKeys':
                    if error.message == "Internal Error":
                        known_errors[api_call] = ('SECSVC-398', "[TrustedEnv] IAM call not in AEL filtered by AAR")
                    else:
                        errors[api_call] = "Remove known error"
                elif api_call == 'icu.UpdateAccessKey':
                    if error.error_code == 'ApiAccessDeniedException':
                        known_errors[api_call] = ('SECSVC-398', "[TrustedEnv] IAM call not in AEL filtered by AAR")
                    else:
                        errors[api_call] = "Remove known error"
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

    def test_T5787_check_AEL_with_MFA_login_password(self):
        errors = {}
        known_errors = {}
        for api_call, params in self.ael_api_calls.items():
            if api_call.startswith('eim'): # authent login/mdp not supported
                continue
            func = self.osc_sdk
            for elt in api_call.split('.'):
                func = getattr(func, elt)
            try:
                if not params:
                    params= {}
                params['exec_data'] = {osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                       osc_api.EXEC_DATA_CERTIFICATE: [self.client_cert[2], self.client_cert[1]]}
                func(**params)
            except OscApiException as error:
                if api_call == 'icu.UpdateAccessKey':
                    if error.error_code == 'ApiAccessDeniedException':
                        known_errors[api_call] = ('SECSVC-398', "[TrustedEnv] IAM call not in AEL filtered by AAR")
                    else:
                        errors[api_call] = "Remove known error"
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


    def test_T5788_check_call_with_ak_sk(self):
        errors = {}
        known_errors = {}
        for api_call, params in self.aksk_api_calls.items():
            func = self.osc_sdk
            for elt in api_call.split('.'):
                func = getattr(func, elt)
            try:
                if not params:
                    params= {}
                func(**params)
            except OscApiException as error:
                if api_call == "eim.ListUsers":
                    if error.message == "Internal Error":
                        known_errors[api_call] = ('SECSVC-398', "[TrustedEnv] IAM call not in AEL filtered by AAR")
                    else:
                        errors[api_call] = "Remove known error"
                else:
                    errors[api_call] = error

        for api_call, error in errors.items():
            self.logger.warning("%s: %s", api_call, error)
        assert not errors

        if known_errors:
            for api_call, error in known_errors.items():
                self.logger.warning("%s: %s", api_call, error)
            known_error(list(known_errors.values())[0][0], list(known_errors.values())[0][1])

    def test_T5789_check_call_with_login_password(self):
        errors = {}
        for api_call, params in self.mdp_api_calls.items():
            func = self.osc_sdk
            for elt in api_call.split('.'):
                func = getattr(func, elt)
            try:
                if not params:
                    params= {}
                params['exec_data'] = {osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword}
                func(**params)
            except OscApiException as error:
                errors[api_call] = error

        for api_call, error in errors.items():
            self.logger.warning("%s: %s", api_call, error)
        assert not errors

    def test_T5790_check_call_without_authent(self):
        errors = {}
        for api_call, params in self.pub_api_calls.items():
            func = self.osc_sdk
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

    def test_T5791_create_infinite_ak_sk(self):
        try:
            self.osc_sdk.api.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                                        osc_api.EXEC_DATA_CERTIFICATE: [self.client_cert[2], self.client_cert[1]]},)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_tools.check_oapi_error(error, 4118)

    def test_T5792_create_finite_ak_sk(self):
        self.osc_sdk.api.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                                    osc_api.EXEC_DATA_CERTIFICATE: [self.client_cert[2], self.client_cert[1]]},
                                          ExpirationDate=self.exp_date)

    def test_T5793_update_aar_without_cert(self):
        try:
            self.osc_sdk.api.UpdateApiAccessRule(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk,
                                                            osc_api.EXEC_DATA_CERTIFICATE: [self.client_cert[2], self.client_cert[1]]},
                                                  ApiAccessRuleId=self.aar_id, Description="AAR fo AAP and TrustedEnv", IpRanges=['0.0.0.0/0'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_tools.check_oapi_error(error, 4118)
