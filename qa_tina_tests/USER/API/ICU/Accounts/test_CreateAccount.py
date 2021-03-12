
import string

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_CreateAccount(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.asquotas = {'COUNT_ACCOUNT_CREATED_ACCOUNTS': 2}
        super(Test_CreateAccount, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateAccount, cls).teardown_class()

    def generate_params(self, customer_id=None, email=None):
        if not customer_id:
            customer_id = id_generator(size=8, chars=string.digits)
        if not email:
            email = 'qa+test_create_account_{}@outscale.com'.format(customer_id)
        params = {'City': 'Saint_Cloud', 'CompanyName': 'Outscale', 'Country': 'France',
                  'CustomerId': customer_id,
                  'Email': email, 'FirstName': 'Test_user', 'LastName': 'Test_Last_name',
                  'Password': misc.id_generator(size=20, chars=string.digits+string.ascii_letters), 'ZipCode': '92210'}
        self.logger.info(params)
        return params

    def test_T541_no_param(self):
        try:
            self.a1_r1.icu.CreateAccount()
            assert False, 'CreateAccount should have failed'
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", 'Parameter cannot be empty: City')

    @pytest.mark.region_admin
    def test_T544_required_param_default_account(self):
        account_info = self.generate_params()
        ret = None
        try:
            ret = self.a1_r1.icu.CreateAccount(**account_info)
            assert ret.response.Account.Email == account_info['Email']
        finally:
            if ret:
                # delete account
                self.a1_r1.xsub.terminate_account(pid=ret.response.Account.AccountPid)
                # self.a1_r1.identauth.IdauthAccountAdmin.deleteAccount(account_id=self.a1_r1.config.region.get_info(constants.AS_IDAUTH_ID),
                #                                                      principal={"accountPid": ret.response.Account.AccountPid}, forceRemoval="true")

    def test_T556_duplicate_email_address(self):
        try:
            # get account email
            # TODO create an account and get this account, we should not use the test account it can break the other tests
            ret = self.a1_r1.icu.GetAccount()
            email = ret.response.Account.Email
            # generate params
            params = self.generate_params(email=email)
            self.a1_r1.icu.CreateAccount(**params)
            assert False, 'CreateAccount should have failed'
        except OscApiException as error:
            assert_error(error, 400, "DuplicateEmailAddress", 'Account already exists with this email address.')

    def test_T557_invalid_email_address(self):
        try:
            # get account email
            email = 'test@test'
            # generate params
            ret = self.generate_params(email=email)
            self.a1_r1.icu.CreateAccount(**ret)
            assert False, 'CreateAccount should have failed'
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterValue",
                         r"Invalid value received for 'EmailAddress': test@test. Supported patterns: ^.+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$")

    # def test_T757_without_quota(self):
    # TODO: change quota of the user to 0 to be able to execute the test

    def test_T545_invalid_customer_id(self):
        name = 'foo'
        try:
            ret = self.generate_params(customer_id=name)
            ret = self.a1_r1.icu.CreateAccount(**ret)
            assert False, 'CreateAccount should have failed'
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterValue", "Value of parameter 'CustomerID' must contain numeric characters only. Received: foo")
