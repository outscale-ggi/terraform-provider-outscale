from qa_common_tools.test_base import OscTestSuite
import pytest
from qa_common_tools import misc
from qa_common_tools.misc import id_generator, assert_error
from osc_sdk_pub.default_config import DefaultPubConfig
from osc_sdk_pub.osc_api.osc_icu_api import OscIcuApi
from osc_sdk_pub.osc_api import AuthMethod
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.account_tools import create_account, delete_account


@pytest.mark.region_admin
class Test_Strong_Password(OscTestSuite):

    @classmethod
    def setup_method(self, method):
        self.user = None
        OscTestSuite.setup_method(self, method)
        try:
            self.email = '{}@outscale.com'.format(id_generator(prefix='qa+teststrongpassword+'))
            self.password = misc.id_generator(size=20)
            self.user = create_account(self.a1_r1, account_info={'email_address': self.email, 'password': self.password})
            self.a1_r1.icu.SendResetPasswordEmail(Email=self.email)
            self.rettoken = self.a1_r1.identauth.IdauthPasswordToken.createAccountPasswordToken(accountEmail=self.email, account_id=self.user)
            ret = self.a1_r1.intel.accesskey.find_by_user(owner=self.user)
            keys = ret.response.result[0]
            config = DefaultPubConfig(ak=keys.name, sk=keys.secret, login=self.email, password=self.password, region_name=self.a1_r1.config.region.name)
            self.icu = OscIcuApi(service='icu', config=config)
        except:
            try:
                self.teardown_method()
            except:
                pass
            raise

    @classmethod
    def teardown_method(self, method):
        try:
            if self.user:
                delete_account(self.a1_r1, self.user)
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T4330_too_weak_password_with_pattern(self):
        new_password = "totototo1234(!)"
        try:
            self.icu.ResetAccountPassword(auth=AuthMethod.Empty, Token=self.rettoken.response.passwordToken, Password=new_password)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'PasswordPolicyViolation', 'Password strength score (3) is too low: at least 4 out'
                                                                ' of 4 level is expected')
        try:
            self.icu.UpdateAccount(Password=new_password)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'PasswordPolicyViolation', 'Password strength score (3) is too low: at least 4 out'
                                                                ' of 4 level is expected')

    def test_T4331_too_weak_password_too_short(self):
        try:
            new_password = "toTO93(!)"
            self.icu.ResetAccountPassword(auth=AuthMethod.Empty, Token=self.rettoken.response.passwordToken, Password=new_password)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'PasswordPolicyViolation', 'Password strength score (3) is too low: at least 4 out'
                                                                ' of 4 level is expected')

    def test_T4332_too_weak_password_missing_sc(self):
        new_password = "lflfljkhfLFKJHFJH093540733"
        self.icu.ResetAccountPassword(auth=AuthMethod.Empty, Token=self.rettoken.response.passwordToken, Password=new_password)

    def test_T4333_too_weak_password_missing_chars(self):
        new_password = "(!)FKJHFJH093540733"
        self.icu.ResetAccountPassword(auth=AuthMethod.Empty, Token=self.rettoken.response.passwordToken, Password=new_password)

    def test_T4334_too_weak_password_missing_upper_chars(self):
        new_password = "lflfljkhf(!)093540733"
        self.icu.ResetAccountPassword(auth=AuthMethod.Empty, Token=self.rettoken.response.passwordToken, Password=new_password)

    def test_T4335_too_weak_password_missing_number(self):
        new_password = "lflfljkhfLFKJHFJH(!)"
        self.icu.ResetAccountPassword(auth=AuthMethod.Empty, Token=self.rettoken.response.passwordToken, Password=new_password)

    def test_T4336_too_weak_password_only_chars(self):
        new_password = "aqszrfegdtyrufidsksd"
        self.icu.ResetAccountPassword(auth=AuthMethod.Empty, Token=self.rettoken.response.passwordToken, Password=new_password)
