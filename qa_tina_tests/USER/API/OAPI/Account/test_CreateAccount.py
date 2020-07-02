# pylint: disable=missing-docstring
import string
import pytest
from qa_test_tools import misc
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.specs.check_tools import check_oapi_response


class Test_CreateAccount(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.ASQUOTAS = {'COUNT_ACCOUNT_CREATED_ACCOUNTS': 2}
        super(Test_CreateAccount, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateAccount, cls).teardown_class()

    def generate_params(self, customer_id=None, email=None):
        if not customer_id:
            customer_id = misc.id_generator(size=8, chars=string.digits)
        if not email:
            email = 'qa+test_create_account_{}@outscale.com'.format(customer_id)
        params = {'City': 'Saint_Cloud', 'CompanyName': 'Outscale', 'Country': 'France',
                  'CustomerId': customer_id,
                  'Email': email, 'FirstName': 'Test_user', 'LastName': 'Test_Last_name',
                  'ZipCode': '92210'}
        self.logger.info(params)
        return params

    def test_T4756_no_param(self):
        try:
            self.a1_r1.oapi.CreateAccount()
            assert False, 'CreateAccount should have failed'
        except OscApiException as error:
            misc.assert_error(error, 400, "7000", "MissingParameter")

    def test_T4757_required_param_default_account(self):
        account_info = self.generate_params()
        ret = None
        try:
            ret = self.a1_r1.oapi.CreateAccount(**account_info)
            check_oapi_response(ret.response, "CreateAccountResponse")
            for attr in account_info.keys():
                if not hasattr(ret.response.Account, attr):
                    assert False, 'Could not find attribute {} in response'.format(attr)
        finally:
            if ret:
                # delete account
                self.a1_r1.xsub.terminate_account(pid=ret.response.Account.AccountId)

    def test_T4758_duplicate_email_address(self):
        try:
            # get account email
            # TODO create an account and get this account, we should not use the test account it can break the other tests
            ret = self.a1_r1.oapi.ReadAccounts()
            email = ret.response.Accounts[0].Email
            # generate params
            params = self.generate_params(email=email)
            self.a1_r1.oapi.CreateAccount(**params)
            assert False, 'CreateAccount should have failed'
        except OscApiException as error:
            misc.assert_error(error, 409, "9007", 'ResourceConflict')

    def test_T4759_invalid_email_address(self):
        try:
            # get account email
            email = 'test@test'
            # generate params
            ret = self.generate_params(email=email)
            self.a1_r1.oapi.CreateAccount(**ret)
            assert False, 'CreateAccount should have failed'
        except OscApiException as error:
            misc.assert_error(error, 400, "4047", "InvalidParameterValue")

    def test_T4760_invalid_customer_id(self):
        name = 'foo'
        try:
            ret = self.generate_params(customer_id=name)
            self.a1_r1.oapi.CreateAccount(**ret)
            assert False, 'CreateAccount should have failed'
        except OscApiException as error:
            misc.assert_error(error, 400, "4047", "InvalidParameterValue")
