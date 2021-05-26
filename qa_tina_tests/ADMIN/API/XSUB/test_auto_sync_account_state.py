import datetime
import time

from qa_sdk_common.exceptions.osc_exceptions import OscException, OscApiException
from qa_test_tools.account_tools import create_account
from qa_test_tools.config import config_constants as constants
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.test_base import OscTestSuite


class Test_auto_sync_account_state(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_auto_sync_account_state, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_auto_sync_account_state, cls).teardown_class()

    def test_T1827_no_param(self):
        users = []
        # create user(s)
        try:
            for _ in range(20):
                try:
                    users.append(create_account(self.a1_r1, no_loop=True))
                except Exception as error:
                    pass
            errors = []
            for user in users:
                try:
                    self.a1_r1.identauth.IdauthAccountAdmin.disableAccount(
                        account_id=self.a1_r1.config.region.get_info(constants.AS_IDAUTH_ID),
                        principal={"accountPid": user})
                except OscException as error:
                    errors.append(user)
            ret = self.a1_r1.xsub.auto_sync_account_state()
            for user in users:
                ret = self.a1_r1.xsub.get_account(pid=user)
                assert ret.response.result.account.username == user
                if user not in errors:
                    if ret.response.result.account.status.identauth != 'INACTIVE' or ret.response.result.account.status.intel != 'disabled':
                        errors.append(user)
            if errors:
                # self.logger.info("Some users ({}) could not be disabled : {}".format(len(errors), errors))
                raise OscTestException("Error(s) occurred while disabling users.")
        except OscException as error:
            raise error
        finally:
            undeleted_users = []
            errors = []
            for user in users:
                try:
                    self.a1_r1.xsub.terminate_account(pid=user)
                    start = datetime.datetime.now()
                    ret = None
                    while datetime.datetime.now() - start < datetime.timedelta(0, 30, 0):
                        try:
                            ret = self.a1_r1.intel.user.gc(username=user)
                            break
                        except OscApiException as error:
                            # accept errors due to unauthorized calling simultaneously user.gc (--> error 200,0,'locked')
                            if error.status_code != 200 or error.message != 'locked' or error.error_code != 0:
                                raise error
                            time.sleep(2)
                except OscException as error:
                    undeleted_users.append(user)
                    errors.append(error)
            if undeleted_users:
                raise OscTestException("Could not delete user(s) (pid(s) = {}, error(s) = {})".format(undeleted_users, errors))
