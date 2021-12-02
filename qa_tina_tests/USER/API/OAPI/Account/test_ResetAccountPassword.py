import string

from qa_sdk_common.config import DefaultAccount, DefaultRegion
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_sdk_pub.osc_api import DefaultPubConfig
from qa_sdk_pub.osc_api.osc_oapi_api import OscOApi
from specs import check_oapi_error
from qa_test_tools import misc, account_tools
from qa_test_tools.config import config_constants
from qa_tina_tools.test_base import OscTinaTest


class Test_ResetAccountPassword(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.pid = None
        cls.rettoken = None
        cls.icu = None
        cls.new_password = None
        cls.email = '{}@outscale.com'.format(misc.id_generator(prefix='qa+Test_ResetAccountPassword+'))
        cls.password = misc.id_generator(size=20, chars=string.digits + string.ascii_letters)
        cls.oapi = None

        super(Test_ResetAccountPassword, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ResetAccountPassword, cls).teardown_class()

    def setup_method(self, method):
        super(Test_ResetAccountPassword, self).setup_method(method)
        self.pid = account_tools.create_account(self.a1_r1, account_info={'email_address': self.email, 'password': self.password})
        self.a1_r1.oapi.SendResetPasswordEmail(Email=self.email)
        self.rettoken = self.a1_r1.identauth.IdauthPasswordToken.createAccountPasswordToken(accountEmail=self.email, account_id=self.pid)
        config = DefaultPubConfig(account=DefaultAccount(login=self.email, password=self.password),
                                  region=DefaultRegion(name=self.a1_r1.config.region.name,
                                                       verify=self.a1_r1.config.region.get_info(config_constants.VALIDATE_CERTS)))
        self.oapi = OscOApi(service='oapi', config=config)
        self.new_password = misc.id_generator(size=20)

    def teardown_method(self, method):
        try:
            if self.pid:
                account_tools.delete_account(self.a1_r1, self.pid)
        finally:
            super(Test_ResetAccountPassword, self).teardown_method(method)

    def test_T4764_non_authenticated(self):
        ret = self.oapi.ResetAccountPassword(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                                             Token=self.rettoken.response.passwordToken, Password=self.new_password)
        ret.check_response()

    def test_T4765_with_the_same_password(self):
        try:
            self.oapi.ResetAccountPassword(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                                           Token=self.rettoken.response.passwordToken, Password=self.password)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 9074)
