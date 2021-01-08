from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.account_tools import create_account, delete_account
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_create_account(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create_account, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_create_account, cls).teardown_class()

    def test_T2607_incorrect_quota(self):
        pid = None
        try:
            maxaccount = 0
            items = self.a1_r1.identauth.IdauthEntityLimit.getAccountLimits(accountPid=self.a1_r1.config.account.account_id).response.limits.items
            for item in items:
                if item.article == 'COUNT_ACCOUNT_CREATED_ACCOUNTS':
                    maxaccount = item.value
                    break
            self.a1_r1.identauth.IdauthEntityLimit.putAccountLimits(accountPid=self.a1_r1.config.account.account_id,
                                                                    limits={'items': [{'article': 'COUNT_ACCOUNT_CREATED_ACCOUNTS', 'value': 0}]})
            pid = create_account(self.a1_r1, creator=self.a1_r1.config.account.account_id)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            if err.error_code == 'too-many-accounts-created' and err.status_code == 200:
                known_error('TINA-4758', 'Error status code when creating an account without quota')
            assert False, 'Remove known error code'
            assert_error(err, 400, 'too-many-accounts-created', 'Limit [COUNT_ACCOUNT_CREATED_ACCOUNTS] is exceeded for entity')
        finally:
            if maxaccount:
                self.a1_r1.identauth.IdauthEntityLimit.putAccountLimits(accountPid=self.a1_r1.config.account.account_id, limits={'items': [{"article": 'COUNT_ACCOUNT_CREATED_ACCOUNTS', "value": maxaccount}]})
            if pid:
                delete_account(self.a1_r1, pid)
