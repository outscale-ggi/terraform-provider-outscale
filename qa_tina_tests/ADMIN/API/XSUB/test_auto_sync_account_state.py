from qa_common_tools import constants
from osc_common.exceptions.osc_exceptions import OscException, OscTestException
from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.account_tools import create_account


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
            for _ in range(200):
                users.append(create_account(self.a1_r1))
            errors = []
            for user in users:
                try:
                    self.a1_r1.identauth.IdauthAccountAdmin.disableAccount(
                        account_id=self.a1_r1.config.region.get_info(constants.AS_IDAUTH_ID),
                        principal={"accountPid": user})
                except OscException as error:
                    errors.append(user)
                    pass
            ret = self.a1_r1.xsub.auto_sync_account_state()
            for user in users:
                ret = self.a1_r1.xsub.get_account(pid=user)
                assert ret.response.result.account.username == user
                if user not in errors:
                    if ret.response.result.account.status.identauth != 'INACTIVE' or ret.response.result.account.status.intel != 'disabled':
                        errors.append(user)
            if errors:
                self.logger.info("Some users ({}) could not be disabled : {}".format(len(errors), errors))
                raise OscTestException("Error(s) occurred while disabling users.")
        except OscException as error:
            raise error
        finally:
            undeleted_users = []
            for user in users:
                try:
                    self.a1_r1.xsub.terminate_account(pid=user)
                    self.a1_r1.intel.user.delete(username=user)
                    self.a1_r1.intel.user.gc(username=user)
                    self.a1_r1.identauth.IdauthAccountAdmin.deleteAccount(
                        account_id=self.a1_r1.config.region.get_info(constants.AS_IDAUTH_ID),
                        principal={"accountPid": user}, forceRemoval="true")
                except OscException as error:
                    undeleted_users.append(user)
            if undeleted_users:
                raise OscTestException("Could not delete user(s) (pid(s) = " + str(undeleted_users) + ").")
