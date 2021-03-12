

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_ListGroupsForUser(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ListGroupsForUser, cls).setup_class()
        cls.group = None
        cls.user = None
        group_name = id_generator(prefix='group_')
        user_name = id_generator(prefix='user_')
        try:
            cls.group = cls.a1_r1.eim.CreateGroup(GroupName=group_name).response.CreateGroupResult.Group
            cls.user = cls.a1_r1.eim.CreateUser(UserName=user_name).response.CreateUserResult.User
            cls.a1_r1.eim.AddUserToGroup(UserName=cls.user.UserName, GroupName=cls.group.GroupName)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.user:
                cls.a1_r1.eim.RemoveUserFromGroup(UserName=cls.user.UserName, GroupName=cls.group.GroupName)
                cls.a1_r1.eim.DeleteUser(UserName=cls.user.UserName)
            if cls.group:
                cls.a1_r1.eim.DeleteGroup(GroupName=cls.group.GroupName)

        finally:
            super(Test_ListGroupsForUser, cls).teardown_class()

    def test_T3963_with_required_params(self):
        ret = self.a1_r1.eim.ListGroupsForUser(UserName=self.user.UserName)
        assert len(ret.response.ListGroupsForUserResult.Groups) == 1
        ret = self.a1_r1.eim.GetGroup(GroupName=self.group.GroupName)
        assert ret.response.GetGroupResult.Group.GroupName == self.group.GroupName

    def test_T3964_with_invalid_group_name(self):
        try:
            self.a1_r1.eim.ListGroupsForUser(UserName='tota')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 404, 'NoSuchEntity', 'Cannot find user [path=*, name=tota] for account [arn:aws:iam::{}:account]'
                         .format(self.a1_r1.config.account.account_id))

    def test_T3965_with_group_name_from_other_account(self):
        try:
            self.a2_r1.eim.ListGroupsForUser(UserName=self.user.UserName)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 404, 'NoSuchEntity', 'Cannot find user [path=*, name={}] for account [arn:aws:iam::{}:account]'
                         .format(self.user.UserName, self.a2_r1.config.account.account_id))

    def test_T4012_without_params(self):
        try:
            self.a1_r1.eim.ListGroupsForUser()
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'UserName may not be empty')
