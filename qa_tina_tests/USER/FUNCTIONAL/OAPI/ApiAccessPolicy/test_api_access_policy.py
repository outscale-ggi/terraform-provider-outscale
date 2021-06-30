from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_test_tools import misc
from qa_test_tools.config import config_constants
from qa_tina_tools.tina.setup_aap import OscTestAAP

class Test_ApiAccessPolicy(OscTestAAP):

    def test_T0000_as_authent(self):
        self.logger.debug("################")
        self.logger.debug("#     TEST     #")
        self.logger.debug("################")
        # TODO: RM (test just for debug)
        ret = self.osc_sdk.api.CreateAccessKey(ExpirationDate=self.exp_date)
        self.logger.debug(ret.response.display())

        info = self.osc_sdk.api.CreateAccessKey(exec_data={osc_api.EXEC_DATA_DRY_RUN: True},
                                                ExpirationDate=self.exp_date)
        authorization = info['headers']['Authorization']
        #cred = authorization.split(' ')[1].split('=')[1].split('/')[0]
        #date = authorization.split(' ')[1].split('/')[1]
        reg_name = authorization.split(' ')[1].split('/')[2]
        service = authorization.split(' ')[1].split('/')[3]
        #signature = authorization.split(' ')[3].split('=')[1]
        #body = "{}\n{}\n{}\n{}".format(
        #    authorization.split(' ')[0],
        #    info['headers']['X-Osc-Date'],
        #    '/'.join(authorization.split(' ')[1].split('/')[1:])[:-1],
        #    hashlib.sha256(info['canonical_request'].encode('utf-8')).hexdigest()
        #    )
        #ret = self.osc_sdk.identauth.IdauthAuthentication.authenticate(
        #    account_id=self.osc_sdk.config.region.get_info(config_constants.AS_IDAUTH_ID),
        #    credentials=cred,
        #    signature=signature,
        #    credentialsType="ACCESS_KEY",
        #    signatureMethod="OSC_V4",
        #    body=body,
        #    signatureTokens=[
        #        {'value': date, 'key': 'Date'},
        #        {'value': reg_name, 'key': 'Region'},
        #        {'value': service, 'key': 'Service'},
        #    ],
        #    conditionParams=[{'value': misc.get_nat_ips(self.osc_sdk.config.region)[0].split('/')[0], 'key': {'vendor': 'idauth', 'id': 'SourceIp'}}],
        #)
        #self.logger.debug(ret.response.display())

        #ret = self.osc_sdk.identauth.IdauthAuthorization.isAuthorized(
        #    account_id=self.osc_sdk.config.region.get_info(config_constants.AS_IDAUTH_ID),
        #    action={'vendor': service, 'operation': 'CreateAccessKey'},
        #    conditionParams=[
        #        {'value': misc.get_nat_ips(self.osc_sdk.config.region)[0].split('/')[0], 'key': {'vendor': 'idauth', 'id': 'SourceIp'}},
        #        {'value': open(self.client_cert[2]).read(), 'key': {'vendor': 'idauth', 'id': 'ApiAccessCert'}}
        #        ],
        #    principal={'accountPid': self.account_pid},
        #    resources={'namespace': self.account_pid, 'region': reg_name, 'relativeId': '*', 'vendor': service},
        #    )
        #self.logger.debug(ret.response.display())

        self.logger.debug("# Call in AEL, without certificate, with region")
        ret = self.osc_sdk.identauth.IdauthAuthorization.isAuthorized(
            account_id=self.osc_sdk.config.region.get_info(config_constants.AS_IDAUTH_ID),
            action={'vendor': service, 'operation': 'CreateAccessKey'},
            conditionParams=[{'value': misc.get_nat_ips(self.osc_sdk.config.region)[0].split('/')[0], 'key': {'vendor': 'idauth', 'id': 'SourceIp'}}],
            principal={'accountPid': self.account_pid},
            resources={'namespace': self.account_pid, 'region': reg_name, 'relativeId': '*', 'vendor': service},
            )
        self.logger.debug(ret.response.display())

        self.logger.debug("# Call in AEL, without certificate, without region")
        ret = self.osc_sdk.identauth.IdauthAuthorization.isAuthorized(
            account_id=self.osc_sdk.config.region.get_info(config_constants.AS_IDAUTH_ID),
            action={'vendor': service, 'operation': 'CreateAccessKey'},
            conditionParams=[{'value': misc.get_nat_ips(self.osc_sdk.config.region)[0].split('/')[0], 'key': {'vendor': 'idauth', 'id': 'SourceIp'}}],
            principal={'accountPid': self.account_pid},
            resources={'namespace': self.account_pid, 'relativeId': '*', 'vendor': service},
            )
        self.logger.debug(ret.response.display())

        self.logger.debug("# Call not in AEL, without certificate, with region")
        ret = self.osc_sdk.identauth.IdauthAuthorization.isAuthorized(
            account_id=self.osc_sdk.config.region.get_info(config_constants.AS_IDAUTH_ID),
            action={'vendor': service, 'operation': 'ReadVms'},
            conditionParams=[{'value': misc.get_nat_ips(self.osc_sdk.config.region)[0].split('/')[0], 'key': {'vendor': 'idauth', 'id': 'SourceIp'}}],
            principal={'accountPid': self.account_pid},
            resources={'namespace': self.account_pid, 'region': reg_name, 'relativeId': '*', 'vendor': service},
            )
        self.logger.debug(ret.response.display())

        self.logger.debug("# Call not in AEL, without certificate, without region")
        ret = self.osc_sdk.identauth.IdauthAuthorization.isAuthorized(
            account_id=self.osc_sdk.config.region.get_info(config_constants.AS_IDAUTH_ID),
            action={'vendor': service, 'operation': 'ReadVms'},
            conditionParams=[{'value': misc.get_nat_ips(self.osc_sdk.config.region)[0].split('/')[0], 'key': {'vendor': 'idauth', 'id': 'SourceIp'}}],
            principal={'accountPid': self.account_pid},
            resources={'namespace': self.account_pid, 'relativeId': '*', 'vendor': service},
            )
        self.logger.debug(ret.response.display())


    def test_T5784_check_AEL_wihtout_MFA_ak_sk(self):
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

    def test_T5785_check_AEL_wihtout_MFA_login_mdp(self):
        errors = {}
        for api_call, params in self.ael_api_calls.items():
            func = self.osc_sdk
            for elt in api_call.split('.'):
                func = getattr(func, elt)
            try:
                if not params:
                    params = {}
                params['exec_data'] = {osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword}
                ret = func(**params)
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


    def test_T5786_check_AEL_with_MFA_ak_sk(self):
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

    def test_T5787_check_AEL_with_MFA_login_password(self):
        errors = {}
        for api_call, params in self.ael_api_calls.items():
            func = self.osc_sdk
            for elt in api_call.split('.'):
                func = getattr(func, elt)
            try:
                if not params:
                    params= {}
                params['exec_data'] = {osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
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

    def test_T5788_check_call_with_ak_sk(self):
        errors = {}
        for api_call, params in self.aksk_api_calls.items():
            func = self.osc_sdk
            for elt in api_call.split('.'):
                func = getattr(func, elt)
            try:
                if not params:
                    params= {}
                func(**params)
                #self.logger.debug(ret.response.display())
            except OscApiException as error:
                errors[api_call] = error

        for api_call, error in errors.items():
            self.logger.warning("%s: %s", api_call, error)
        assert not errors

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
                #self.logger.debug(ret.response.display())
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
            misc.assert_oapi_yml(error, 4118)

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
            misc.assert_oapi_yml(error, 4118)
