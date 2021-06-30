import datetime
import os
import string

import pytest

from qa_sdk_common.exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_sdks import OscSdk
from qa_test_tools import misc
from qa_test_tools.account_tools import create_account, delete_account
from qa_test_tools.config import OscConfig
from qa_test_tools.misc import assert_oapi_yml, assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina import create_tools


CLIENT_CERT_CN1 = 'client.qa1'


@pytest.mark.region_admin
class Test_UpdateApiAccessPolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateApiAccessPolicy, cls).setup_class()
        cls.account_sdk = None

    def setup_method(self, method):
        super(Test_UpdateApiAccessPolicy, self).setup_method(method)
        try:
            email = 'qa+{}@outscale.com'.format(misc.id_generator(prefix='api_access_policy').lower())
            password = misc.id_generator(size=20, chars=string.digits + string.ascii_letters)
            account_info = {'city': 'Saint_Cloud', 'company_name': 'Outscale', 'country': 'France',
                            'email_address': email, 'firstname': 'Test_user', 'lastname': 'Test_Last_name',
                            'password': password, 'zipcode': '92210'}
            account_pid = create_account(self.a1_r1, account_info)
            keys = self.a1_r1.intel.accesskey.find_by_user(owner=account_pid).response.result[0]

            config = OscConfig.get_with_keys(self.a1_r1.config.region.az_name, keys.name, keys.secret, account_pid,
                                             login=email, password=password)
            self.account_sdk = OscSdk(config=config)
        except Exception as error:
            try:
                self.teardown_method(method)
            except Exception as err:
                raise err
            finally:
                raise error

    def teardown_method(self, method):
        try:
            delete_account(self.account_sdk, self.account_sdk.config.account.account_id)
        finally:
            OscTestSuite.teardown_method(self, method)

    # create a setup function with account sdk, parameter with ca and update key
    def setup_prerequisites(self, with_aar, with_med):
        ca_pid = None
        aar_id = None
        ca1files = None
        certfiles_ca1cn1 = None
        if with_aar:

            ca1files = create_tools.create_caCertificate_file(root='.', cakey='ca1.key', cacrt='ca1.crt',
                                                              casubject='"/C=FR/ST=Paris/L=Paris/O=outscale/OU=QA/CN=outscale1.com"')

            certfiles_ca1cn1 = create_tools.create_client_certificate_files(
                ca1files[0], ca1files[1],
                root='.', clientkey='ca1cn1.key', clientcsr='ca1cn1.csr', clientcrt='ca1cn1.crt',
                clientsubject='/C=FR/ST=Paris/L=Paris/O=outscale/OU=QA/CN={}'.format(CLIENT_CERT_CN1))

            ca_pid = self.account_sdk.oapi.CreateCa(CaPem=open(ca1files[1]).read(),
                                                    Description="ca1files").response.Ca.CaId

            aar_id = self.account_sdk.oapi.CreateApiAccessRule(CaIds=[ca_pid]).response.ApiAccessRule.ApiAccessRuleId
        if with_med:
            keys = self.a1_r1.intel.accesskey.find_by_user(owner=self.account_sdk.config.account.account_id).response.result
            exp_date = (datetime.datetime.utcnow() + datetime.timedelta(minutes=60)).strftime(
                "%Y-%m-%dT%H:%M:%S.000+0000")
            for key in keys:
                self.account_sdk.identauth.IdauthAccount.updateAccessKey(accessKeyPid=key.name, newExpirationDate=exp_date)
        return ca_pid, aar_id, ca1files, certfiles_ca1cn1

    def teardown_prerequisites(self, ca_pid, aar_id, ca1files, certfiles_ca1cn1):
        cwd = os.getcwd()
        if aar_id:
            self.account_sdk.oapi.DeleteApiAccessRule(ApiAccessRuleId=aar_id)

        if ca_pid:
            self.account_sdk.oapi.DeleteCa(CaId=ca_pid)

        if ca1files:
            os.remove(cwd + "/ca1.crt")
            os.remove(cwd + "/ca1.key")

        if certfiles_ca1cn1:
            os.remove(cwd + "/ca1cn1.crt")
            os.remove(cwd + "/ca1cn1.csr")
            os.remove(cwd + "/ca1cn1.key")

    def test_T5727_login_password(self):
        ret = self.account_sdk.oapi.UpdateApiAccessPolicy(
            exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword},
            MaxAccessKeyExpirationSeconds=0, RequireTrustedEnv=False)
        ret.check_response()

    # TODO PQA-3036: <global> Add all others tests with ak/sk authentication
    def test_T5767_ak_sk(self):
        ret = self.account_sdk.oapi.UpdateApiAccessPolicy(
            exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk},
            MaxAccessKeyExpirationSeconds=0, RequireTrustedEnv=False)
        ret.check_response()

    # TODO PQA-3036: /!\ when update succeed with RequireTrustedEnv=True MFA authent will be required for teardown

    # TODO PQA-3036:     (re-set with RequireTrustedEnv=False with MFA authent)
    def test_T5768_multi_athent(self):
        ret = self.account_sdk.oapi.UpdateApiAccessPolicy(
            exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                       osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk},
            MaxAccessKeyExpirationSeconds=0, RequireTrustedEnv=False)
        ret.check_response()

    # TODO PQA-3036: Add tests
    def test_T5769_with_negative_max_access_key_expiration(self):
        try:
            self.account_sdk.oapi.UpdateApiAccessPolicy(DryRun=0, MaxAccessKeyExpirationSeconds=-4354,
                                                        RequireTrustedEnv=False)
        except OscApiException as error:
            assert_oapi_yml(error, 4110)

    def test_T5770_dry_run_with_zero(self):
        try:
            self.account_sdk.oapi.UpdateApiAccessPolicy(DryRun=0,
            MaxAccessKeyExpirationSeconds=0, RequireTrustedEnv=False)
        except OscApiException as error:
            assert_oapi_yml(error, 4110)

    # TODO PQA-3036:  - with dry run ==> ok
    def test_T5771_dry_run_true(self):
        ret = self.account_sdk.oapi.UpdateApiAccessPolicy(DryRun=True,
            MaxAccessKeyExpirationSeconds=0, RequireTrustedEnv=False)
        assert_dry_run(ret)

    # TODO PQA-3036:  - without MaxAccessKeyExpirationSeconds ==> ko
    def test_T5772_without_max_access_key(self):
        try:
            ret = self.account_sdk.oapi.UpdateApiAccessPolicy(RequireTrustedEnv=False)
            ret.check_response()
        except OscApiException as error:
            assert_oapi_yml(error, 7000)

    # TODO PQA-3036:  - without RequireTrustedEnv ==> ko
    def test_T5773_without_require_trusted_env(self):
        try:
            ret = self.account_sdk.oapi.UpdateApiAccessPolicy(MaxAccessKeyExpirationSeconds=0)
            ret.check_response()
        except OscApiException as error:
            assert_oapi_yml(error, 7000)

    # TODO PQA-3036:  - with invalid MaxAccessKeyExpirationSeconds ==> ko
    def test_T5774_with_invalid_max_access_key(self):
        try:
            ret = self.account_sdk.oapi.UpdateApiAccessPolicy(
                MaxAccessKeyExpirationSeconds=99000000, RequireTrustedEnv=False)
            ret.check_response()
        except OscApiException as error:
            assert_oapi_yml(error, 4118)

    # TODO PQA-3036:  - with invalid RequireTrustedEnv ==> ko
    def test_T5775_with_invalid_require_trusted_env(self):
        try:
            ret = self.account_sdk.oapi.UpdateApiAccessPolicy(
                MaxAccessKeyExpirationSeconds=0, RequireTrustedEnv="foo bar")
            ret.check_response()
        except OscApiException as error:
            assert_oapi_yml(error, 4110)

    # TODO PQA-3036:  - (valid functional) with RequireTrustedEnv=True (setup: need ApiAccessRule with CA and ak/sk with expiration date) ==> ok
    def test_T5776_with_require_trusted_env_and_ca_and_ak_sk(self):
        ca1files = None
        certfiles_ca1cn1 = None
        ca_pid = None
        aar_id = None
        ret_aap = None

        try:
            with_aar = True
            with_med = True
            ca_pid, aar_id, ca1files, certfiles_ca1cn1 = self.setup_prerequisites(with_aar, with_med)

            ret_aap = self.account_sdk.oapi.UpdateApiAccessPolicy(
                exec_data={osc_api.EXEC_DATA_CERTIFICATE: [certfiles_ca1cn1[2], certfiles_ca1cn1[1]],
                           osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk},
                MaxAccessKeyExpirationSeconds=3600, RequireTrustedEnv=True)
            ret_aap.check_response()

        except Exception as error:
            raise error

        finally:
            if ret_aap:
                self.account_sdk.oapi.UpdateApiAccessPolicy(
                    exec_data={osc_api.EXEC_DATA_CERTIFICATE: [certfiles_ca1cn1[2], certfiles_ca1cn1[1]],
                               osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk},
                    MaxAccessKeyExpirationSeconds=0, RequireTrustedEnv=False)
            self.teardown_prerequisites(ca_pid, aar_id, ca1files, certfiles_ca1cn1)

    # TODO  - (valid functional) with RequireTrustedEnv=False (setup: need ApiAccessRule with CA and ak/sk with expiration date) ==>
    def test_T5777_with_require_trusted_env_false_and_ca_and_ak_sk(self):
        ca1files = None
        certfiles_ca1cn1 = None
        ca_pid = None
        aar_id = None
        ret_aap = None

        try:
            with_aar = True
            with_med = True
            ca_pid, aar_id, ca1files, certfiles_ca1cn1 = self.setup_prerequisites(with_aar, with_med)

            ret_aap = self.account_sdk.oapi.UpdateApiAccessPolicy(
                exec_data={osc_api.EXEC_DATA_CERTIFICATE: [certfiles_ca1cn1[2], certfiles_ca1cn1[1]],
                           osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk},
                MaxAccessKeyExpirationSeconds=3600, RequireTrustedEnv=False)
            ret_aap.check_response()

        except Exception as error:
            raise error

        finally:
            if ret_aap:
                self.account_sdk.oapi.UpdateApiAccessPolicy(
                    exec_data={osc_api.EXEC_DATA_CERTIFICATE: [certfiles_ca1cn1[2], certfiles_ca1cn1[1]],
                               osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk},
                    MaxAccessKeyExpirationSeconds=0, RequireTrustedEnv=False)
            self.teardown_prerequisites(ca_pid, aar_id, ca1files, certfiles_ca1cn1)

    # TODO PQA-3036:  - with RequireTrustedEnv=True and without ApiAccessRule ==> ko
    def test_T5778_with_require_trusted_env_without_api_access_rule(self):
        try:
            ret = self.account_sdk.oapi.UpdateApiAccessPolicy(MaxAccessKeyExpirationSeconds=3600,
                                                               RequireTrustedEnv=True)
            ret.check_response()
        except OscApiException as error:
            assert_oapi_yml(error, 4118)

    # TODO PQA-3036:  - with RequireTrustedEnv=True and with ApiAccessRule without CA (rule based only on IP) ==> ko
    def test_T5779_with_require_trusted_env_and_with_ApiAccessRule_without_ca(self):
        try:
            self.account_sdk.oapi.UpdateApiAccessPolicy(MaxAccessKeyExpirationSeconds=0, RequireTrustedEnv=True)
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_yml(error, 4118)

    # TODO PQA-3036:  - with RequireTrustedEnv=True and with ak/sk without expiration date ==> ko
    def test_T5781_with_require_trusted_env_and_ak_sk_and_without_expiration_date(self):
        try:
            self.account_sdk.oapi.UpdateApiAccessPolicy(MaxAccessKeyExpirationSeconds=3600, RequireTrustedEnv=True)
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_yml(error, 4118)

    # TODO PQA-3036:  - with RequireTrustedEnv=True and with ak/sk and MaxAccessKeyExpirationSeconds=0 ==> ko
    def test_T5780_with_require_trusted_env_and_with_ak_sk_and_max_access_key_equals_zero(self):
        ca1files = None
        certfiles_ca1cn1 = None
        ca_pid = None
        aar_id = None
        ret_aap = None
        try:
            with_aar = True
            with_med = True
            ca_pid, aar_id, ca1files, certfiles_ca1cn1 = self.setup_prerequisites(with_aar, with_med)

            ret_aap = self.account_sdk.oapi.UpdateApiAccessPolicy(
                exec_data={osc_api.EXEC_DATA_CERTIFICATE: [certfiles_ca1cn1[2], certfiles_ca1cn1[1]]},
                MaxAccessKeyExpirationSeconds=0, RequireTrustedEnv=True)
            ret_aap.check_response()
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_yml(error, 4118)
        finally:
            if ret_aap:
                self.account_sdk.oapi.UpdateApiAccessPolicy(
                    exec_data={osc_api.EXEC_DATA_CERTIFICATE: [certfiles_ca1cn1[2], certfiles_ca1cn1[1]],
                               osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk},
                    MaxAccessKeyExpirationSeconds=0, RequireTrustedEnv=False)
            self.teardown_prerequisites(ca_pid, aar_id, ca1files, certfiles_ca1cn1)
