# pylint: disable=missing-docstring
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import assert_error
from qa_test_tools.misc import id_generator
from qa_test_tools.config import config_constants as constants
from qa_sdk_pub.osc_api import AuthMethod
from qa_test_tools.account_tools import create_account
import string
from qa_test_tools import misc
from qa_sdk_pub import osc_api


class Test_AuthenticateAccount(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_AuthenticateAccount, cls).setup_class()
        try:
            pass
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_AuthenticateAccount, cls).teardown_class()

    def test_T2159_required_param(self):
        ret = self.a1_r1.icu.AuthenticateAccount(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                                                 Login=self.a1_r1.config.account.login, Password=self.a1_r1.config.account.password)
        assert ret.response.Return

    def test_T2160_without_login(self):
        try:
            self.a1_r1.icu.AuthenticateAccount(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty}, Password=self.a1_r1.config.account.password)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'IcuClientException', 'Field Login is required')

    def test_T2161_without_password(self):
        try:
            self.a1_r1.icu.AuthenticateAccount(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty}, Login=self.a1_r1.config.account.login)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'IcuClientException', 'Field Password is required')

    def test_T2162_with_invalid_password(self):
        try:
            self.a1_r1.icu.AuthenticateAccount(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty}, Login=self.a1_r1.config.account.login, Password='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 401, 'AuthFailure', 'Outscale was not able to validate the provided access credentials. Invalid login/password or password has expired.')

    def create_account(self):
        email = 'qa+{}@outscale.com'.format(id_generator(prefix='test_account_'))
        passwd = misc.id_generator(prefix='pwd_', size=20, chars=string.digits+string.ascii_letters)
        pid = create_account(self.a1_r1, account_info={'email_address': email, 'password': passwd})
        return {'email': email, 'password': passwd, 'id': pid}

    def delete_account(self, account_info):
        self.a1_r1.xsub.terminate_account(pid=account_info['id'])
        self.a1_r1.identauth.IdauthAccountAdmin.deleteAccount(account_id=self.a1_r1.config.region.get_info(constants.AS_IDAUTH_ID),
                                                              principal={"accountPid": account_info['id']}, forceRemoval="true")

    def test_T2163_with_disabled_account(self):
        account_info = self.create_account()
        self.a1_r1.xsub.disable_account(pid=account_info['id'])
        try:
            self.a1_r1.icu.AuthenticateAccount(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty}, Login=account_info['email'], Password=account_info['password'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 401, 'DisabledAccount', 'The account is inactive.')
        finally:
            self.delete_account(account_info)

    def test_T2164_with_restricted_account(self):
        account_info = self.create_account()
        self.a1_r1.xsub.restrict_account(pid=account_info['id'])
        try:
            self.a1_r1.icu.AuthenticateAccount(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty}, Login=account_info['email'], Password=account_info['password'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 401, 'RestrictedAccount', 'The account is restricted.')
        finally:
            self.delete_account(account_info)

    def test_T2165_with_terminated_account(self):
        account_info = self.create_account()
        self.a1_r1.xsub.terminate_account(pid=account_info['id'])
        try:
            self.a1_r1.icu.AuthenticateAccount(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty}, Login=account_info['email'], Password=account_info['password'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 401, 'AuthFailure', 'Outscale was not able to validate the provided access credentials. Invalid login/password or password has expired.')

    def test_T2166_with_frozen_account(self):
        account_info = self.create_account()
        self.a1_r1.xsub.freeze_account(pid=account_info['id'])
        try:
            self.a1_r1.icu.AuthenticateAccount(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty}, Login=account_info['email'], Password=account_info['password'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 401, 'FrozenAccount', 'The account is frozen.')
        finally:
            self.delete_account(account_info)
