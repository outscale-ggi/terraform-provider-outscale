import string

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.account_tools import create_account
from qa_test_tools.config import config_constants
from qa_test_tools.misc import id_generator
from qa_tina_tools.test_base import OscTinaTest


class Test_CheckAuthentication(OscTinaTest):

    def test_T4895_without_param(self):
        try:
            self.a1_r1.oapi.CheckAuthentication()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T4744_required_param(self):
        ret = self.a1_r1.oapi.CheckAuthentication(Login=self.a1_r1.config.account.login, Password=self.a1_r1.config.account.password)
        ret.check_response()

    def test_T4745_without_login(self):
        try:
            self.a1_r1.oapi.CheckAuthentication(Password=self.a1_r1.config.account.password)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T4746_without_password(self):
        try:
            self.a1_r1.oapi.CheckAuthentication(Login=self.a1_r1.config.account.login)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T4747_with_invalid_password(self):
        password = id_generator(size=20)
        try:
            self.a1_r1.oapi.CheckAuthentication(Login=self.a1_r1.config.account.login, Password=password)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, '4120', 'InvalidParameterValue')

    def create_account(self):
        email = 'qa+{}@outscale.com'.format(misc.id_generator(prefix='test_account_'))
        passwd = misc.id_generator(prefix='pwd_', size=20, chars=string.digits + string.ascii_letters)
        pid = create_account(self.a1_r1, account_info={'email_address': email, 'password': passwd})
        return {'email': email, 'password': passwd, 'id': pid}

    def delete_account(self, account_info):
        self.a1_r1.xsub.terminate_account(pid=account_info['id'])
        self.a1_r1.identauth.IdauthAccountAdmin.deleteAccount(
            account_id=self.a1_r1.config.region.get_info(config_constants.AS_IDAUTH_ID),
            principal={"accountPid": account_info['id']},
            forceRemoval="true",
        )

    def test_T4748_with_disabled_account(self):
        account_info = self.create_account()
        self.a1_r1.xsub.disable_account(pid=account_info['id'])
        try:
            self.a1_r1.oapi.CheckAuthentication(Login=account_info['email'], Password=account_info['password'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 401, '11001', 'UserAccountProblem')
        finally:
            self.delete_account(account_info)

    def test_T4749_with_restricted_account(self):
        account_info = self.create_account()
        self.a1_r1.xsub.restrict_account(pid=account_info['id'])
        try:
            self.a1_r1.oapi.CheckAuthentication(Login=account_info['email'], Password=account_info['password'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 401, '11001', 'UserAccountProblem')
        finally:
            self.delete_account(account_info)

    def test_T4750_with_terminated_account(self):
        account_info = self.create_account()
        self.a1_r1.xsub.terminate_account(pid=account_info['id'])
        try:
            self.a1_r1.oapi.CheckAuthentication(Login=account_info['email'], Password=account_info['password'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, '4120', 'InvalidParameterValue')

    def test_T4751_with_frozen_account(self):
        account_info = self.create_account()
        self.a1_r1.xsub.freeze_account(pid=account_info['id'])
        try:
            self.a1_r1.oapi.CheckAuthentication(Login=account_info['email'], Password=account_info['password'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 401, '11001', 'UserAccountProblem')
        finally:
            self.delete_account(account_info)
