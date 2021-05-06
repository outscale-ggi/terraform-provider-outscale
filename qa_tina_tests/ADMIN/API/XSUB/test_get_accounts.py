import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import assert_error


# possible statuses : 'ACTIVE' 'INACTIVE' 'RESTRICTED' 'FROZEN' 'TERMINATED'

class Test_get_accounts(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_get_accounts, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_get_accounts, cls).teardown_class()

    def test_T5562_no_param(self):
        ret = self.a1_r1.xsub.get_accounts()
        assert len(ret.response.result.accounts) > 0

    def test_T5564_with_incorrect_statuses(self):
        try:
            self.a1_r1.xsub.get_accounts(statuses=['titi'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 'invalid-parameter-value', None)

    def test_T5565_with_incorrect_statuses_type(self):
        try:
            self.a1_r1.xsub.get_accounts(statuses=5)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 'invalid-parameter-type', None)

    def test_T5566_with_incorrect_usernames(self):
        ret = self.a1_r1.xsub.get_accounts(usernames=['titi'])
        assert len(ret.response.result.accounts) == 0

    def test_T5567_with_incorrect_usernames_type(self):
        try:
            self.a1_r1.xsub.get_accounts(usernames=5)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 'invalid-parameter-type', None)

    def test_T5568_with_unknown_usernames(self):
        ret = self.a1_r1.xsub.get_accounts(usernames=['556556556'])
        assert len(ret.response.result.accounts) == 0

    def test_T5569_with_valid_statuses(self):
        ret = self.a1_r1.xsub.get_accounts(statuses=['ACTIVE', 'FROZEN'])
        for account in ret.response.result.accounts:
            assert account.status in ['ACTIVE', 'FROZEN']

    def test_T5570_with_valid_usernames(self):
        ret = self.a1_r1.xsub.get_accounts(usernames=[self.a1_r1.config.account.account_id])
        assert len(ret.response.result.accounts) == 1
        assert ret.response.result.accounts[0].username == self.a1_r1.config.account.account_id
        assert ret.response.result.accounts[0].status == 'ACTIVE'
