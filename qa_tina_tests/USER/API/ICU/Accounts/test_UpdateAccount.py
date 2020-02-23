# pylint: disable=missing-docstring

from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import id_generator, assert_error
from qa_common_tools.test_base import OscTestSuite


class Test_UpdateAccount(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateAccount, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_UpdateAccount, cls).teardown_class()

    def test_T571_no_param(self):
        try:
            self.a1_r1.icu.UpdateAccount()
            assert False, "The updateAccount call should not succeed."
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == "MissingParameter"
            assert error.message == "The request must contain at least one parameter"

    def test_T572_email_duplicate(self):
        try:
            self.a1_r1.icu.UpdateAccount(Email=self.a2_r1.config.account.login)
            assert False, 'Call with duplicate email should fail'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == "DuplicateEmailAddress"
            assert error.message == 'Account already exists with this email address.'

    def test_T573_email_new(self):
        email = 'qa+T573_{}@outscale.com'.format(id_generator(size=8))
        ret = self.a1_r1.icu.UpdateAccount(Email=email)
        assert ret.response.Return
        ret = self.a1_r1.icu.GetAccount()
        assert ret.response.Account.Email == email

    def test_T574_email_invalid_format(self):
        try:
            self.a1_r1.icu.UpdateAccount(Email='foo')
            assert False, 'Call with invalid account should fail'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Email has invalid format.')

    def test_T4318_with_invalid_password(self):
        try:
            self.a1_r1.icu.UpdateAccount(Password="toto")
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'PasswordPolicyViolation', 'Password strength score (0) is too low: at least 4 out '
                                                                'of 4 level is expected. Warning: Repeats like '
                                                                '"abcabcabc" are only slightly harder to guess than '
                                                                '"abc".. Suggestions: [Add another word or two. Uncommon'
                                                                ' words are better.|Avoid repeated words and characters.]')

    def test_T4317_with_password(self):
        ret = self.a1_r1.icu.UpdateAccount(Password=id_generator(size=20))
        assert ret.response.Return

    # TODO: Add more tests
