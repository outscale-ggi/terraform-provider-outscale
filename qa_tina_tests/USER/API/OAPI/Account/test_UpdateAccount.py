
import string


from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_oapi_error
from qa_test_tools.test_base import OscTestSuite


class Test_UpdateAccount(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateAccount, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_UpdateAccount, cls).teardown_class()

    def generate_params(self):
        params = {'City': 'Toulouse', 'CompanyName': 'Toto', 'Country': 'France', 'FirstName': 'Test_update',
                  'LastName': 'Test_Last_update', 'ZipCode': '31500'}
        self.logger.info(params)
        return params

    def test_T4912_no_param(self):
        try:
            self.a1_r1.oapi.UpdateAccount()
            assert False, "The updateAccount call should not succeed."
        except OscApiException as error:
            assert_oapi_error(error, 400, "MissingParameter", 7000)

    def test_T4913_email_duplicate(self):
        try:
            self.a1_r1.oapi.UpdateAccount(Email=self.a2_r1.config.account.login)
            assert False, 'Call with duplicate email should fail'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', 9073)

    def test_T4914_email_new(self):
        email = 'qa+T573_{}@outscale.com'.format(id_generator(size=8))
        self.a1_r1.oapi.UpdateAccount(Email=email)
        ret = self.a1_r1.oapi.ReadAccounts()
        assert ret.response.Accounts[0].Email == email

    def test_T4915_email_invalid_format(self):
        try:
            self.a1_r1.oapi.UpdateAccount(Email='foo')
            assert False, 'Call with invalid account should fail'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', 4118)

    def test_T4916_with_invalid_parameter(self):
        passwd = id_generator(size=4, chars=string.ascii_lowercase)
        try:
            self.a1_r1.oapi.UpdateAccount(Password=passwd)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', 3001)

    def test_T4917_with_valid_params(self):
        account_info = self.generate_params()
        ret = self.a1_r1.oapi.UpdateAccount(**account_info)
        ret.check_response()
        assert ret.response.Account.City == account_info['City']
        assert ret.response.Account.CompanyName == account_info['CompanyName']
        assert ret.response.Account.Country == account_info['Country']
        assert ret.response.Account.FirstName == account_info['FirstName']
        assert ret.response.Account.LastName == account_info['LastName']
        assert ret.response.Account.ZipCode == account_info['ZipCode']
