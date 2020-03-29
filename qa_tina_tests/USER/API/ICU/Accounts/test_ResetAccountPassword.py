from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.misc import id_generator, assert_error
from qa_common_tools import misc
from osc_common.config.default_public_config import DefaultPubConfig
from osc_sdk_pub.osc_api.osc_icu_api import OscIcuApi
from osc_sdk_pub.osc_api import AuthMethod
from qa_common_tools.account_tools import create_account, delete_account
import string
from osc_common.exceptions.osc_exceptions import OscApiException


class Test_ResetAccountPassword(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.pid = None
        cls.rettoken = None
        cls.icu = None
        cls.new_password = None
        cls.email = '{}@outscale.com'.format(id_generator(prefix='qa+Test_ResetAccountPassword+'))
        cls.password = misc.id_generator(size=20, chars=string.digits + string.ascii_letters)

        super(Test_ResetAccountPassword, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ResetAccountPassword, cls).teardown_class()

    def setup_method(self, method):
        super(Test_ResetAccountPassword, self).setup_method(method)
        self.pid = create_account(self.a1_r1, account_info={'email_address': self.email, 'password': self.password})
        self.a1_r1.icu.SendResetPasswordEmail(Email=self.email)
        self.rettoken = self.a1_r1.identauth.IdauthPasswordToken.createAccountPasswordToken(accountEmail=self.email, account_id=self.pid)
        config = DefaultPubConfig(None, None, login=self.email, password=self.password, region_name=self.a1_r1.config.region.name)
        self.icu = OscIcuApi(service='icu', config=config)
        self.new_password = misc.id_generator(size=20)

    def teardown_method(self, method):
        try:
            if self.pid:
                delete_account(self.a1_r1, self.pid)
        finally:
            super(Test_ResetAccountPassword, self).teardown_method(method)

    def test_T3962_non_authenticated(self):
        self.icu.ResetAccountPassword(auth=AuthMethod.Empty, Token=self.rettoken.response.passwordToken, Password=self.new_password)

    def test_T4671_with_the_same_password(self):
        try:
            self.icu.ResetAccountPassword(auth=AuthMethod.Empty, Token=self.rettoken.response.passwordToken, Password=self.password)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "PasswordPolicyViolation", 'Password must not match previous 10 password(s)')
