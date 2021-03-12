

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_AddUserToGroup(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_AddUserToGroup, cls).setup_class()
        cls.group = None
        cls.user = None

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        group_name = id_generator(prefix='group_name_')
        user_name = id_generator(prefix='user_name_')
        self.group = None
        self.user = None
        try:
            self.group = self.a1_r1.eim.CreateGroup(GroupName=group_name).response.CreateGroupResult.Group
            self.user = self.a1_r1.eim.CreateUser(UserName=user_name).response.CreateUserResult.User
        except:
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.user:
                self.a1_r1.eim.DeleteUser(UserName=self.user.UserName)
            if self.group:
                self.a1_r1.eim.DeleteGroup(GroupName=self.group.GroupName)
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T3948_add_user_to_group_with_required_params(self):
        ret_add = None
        try:
            ret = self.a1_r1.eim.ListGroupsForUser(UserName=self.user.UserName)
            assert not ret.response.ListGroupsForUserResult.Groups
            ret_add = self.a1_r1.eim.AddUserToGroup(UserName=self.user.UserName, GroupName=self.group.GroupName)
            ret = self.a1_r1.eim.ListGroupsForUser(UserName=self.user.UserName)
            assert len(ret.response.ListGroupsForUserResult.Groups) == 1
            assert ret.response.ListGroupsForUserResult.Groups[0].GroupName == self.group.GroupName
        finally:
            if ret_add:
                self.a1_r1.eim.RemoveUserFromGroup(UserName=self.user.UserName, GroupName=self.group.GroupName)

    def test_T3949_add_user_to_group_with_user_name_param(self):
        try:
            self.a1_r1.eim.AddUserToGroup(UserName=self.user.UserName)
            known_error('TINA-4964', 'Incorrect error expected')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'Missing parameter', '')

    def test_T3950_add_user_to_group_with_group_name_param(self):
        try:
            self.a1_r1.eim.AddUserToGroup(GroupName=self.group.GroupName)
            known_error('TINA-4964', 'Incorrect error expected')
            assert False, 'call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'Missing parameter', 'message, test_message')

    def test_T3951_add_user_to_invalid_group_name(self):
        try:
            self.a1_r1.eim.AddUserToGroup(GroupName='tata', UserName=self.user.UserName)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            if 'ows' in err.message:
                known_error('TINA-4959', '[ORN:OWS...] or [ARN:AWS...]')
            assert False, 'Remove known error code'
            assert_error(err, 404, 'NoSuchEntity', 'Cannot find group [path=*, name=tata] for account [orn:ows:idauth::{}:account]'
                         .format(self.a1_r1.config.account.account_id))

    def test_T3952_add_user_to_group_with_group_name_from_other_account(self):
        try:
            self.a2_r1.eim.AddUserToGroup(UserName=self.user.UserName, GroupName=self.group.GroupName)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            if 'ows' in err.message:
                known_error('TINA-4964', '[ORN:OWS...] or [ARN:AWS...]')

            assert False, 'Remove known error code'
            assert_error(err, 404, 'NoSuchEntity', 'Cannot find group [path=*, name={}] for account [orn:ows:idauth::{}:account]'
                         .format(self.user.UserName, self.a2_r1.config.account.account_id))
