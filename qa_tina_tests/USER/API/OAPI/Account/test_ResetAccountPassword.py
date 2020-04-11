import string
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools import misc, account_tools
from qa_sdk_common.config.default_public_config import DefaultPubConfig
from qa_sdk_pub.osc_api.osc_oapi_api import OscOApi
from qa_tina_tools.specs.oapi.check_tools import check_oapi_response
from qa_sdk_common.exceptions.osc_exceptions import OscApiException


class Test_ResetAccountPassword(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.pid = None
        cls.rettoken = None
        cls.icu = None
        cls.new_password = None
        cls.email = '{}@outscale.com'.format(misc.id_generator(prefix='qa+Test_ResetAccountPassword+'))
        cls.password = misc.id_generator(size=20, chars=string.digits + string.ascii_letters)

        super(Test_ResetAccountPassword, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ResetAccountPassword, cls).teardown_class()

    def setup_method(self, method):
        super(Test_ResetAccountPassword, self).setup_method(method)
        self.pid = account_tools.create_account(self.a1_r1, account_info={'email_address': self.email, 'password': self.password})
        self.a1_r1.oapi.SendResetPasswordEmail(Email=self.email)
        self.rettoken = self.a1_r1.identauth.IdauthPasswordToken.createAccountPasswordToken(accountEmail=self.email, account_id=self.pid)
        config = DefaultPubConfig(None, None, login=self.email, password=self.password, region_name=self.a1_r1.config.region.name)
        self.oapi = OscOApi(service='oapi', config=config)
        self.new_password = misc.id_generator(size=20)

    def teardown_method(self, method):
        try:
            if self.pid:
                account_tools.delete_account(self.a1_r1, self.pid)
        finally:
            super(Test_ResetAccountPassword, self).teardown_method(method)

    def test_T4764_non_authenticated(self):
        ret = self.oapi.ResetAccountPassword(authentication=False, Token=self.rettoken.response.passwordToken, Password=self.new_password)
        check_oapi_response(ret.response, 'ResetAccountPasswordResponse')

    def test_T4765_with_the_same_password(self):
        try:
            self.oapi.ResetAccountPassword(authentication=False, Token=self.rettoken.response.passwordToken, Password=self.password)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 409, '9074', 'ResourceConflict')
