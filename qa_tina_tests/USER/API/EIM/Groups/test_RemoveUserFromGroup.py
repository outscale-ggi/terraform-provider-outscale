

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_RemoveUserFromGroup(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_RemoveUserFromGroup, cls).setup_class()
        group_name = id_generator(prefix='group_name_')
        user_name = id_generator(prefix='user_name_')
        cls.group = None
        cls.user = None
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
                cls.a1_r1.eim.DeleteUser(UserName=cls.user.UserName)
            if cls.group:
                cls.a1_r1.eim.DeleteGroup(GroupName=cls.group.GroupName)
        finally:
            super(Test_RemoveUserFromGroup, cls).teardown_class()

    def test_T3983_with_required_params(self):
        ret = self.a1_r1.eim.ListGroupsForUser(UserName=self.user.UserName)
        assert len(ret.response.ListGroupsForUserResult.Groups) == 1
        self.a1_r1.eim.RemoveUserFromGroup(GroupName=self.group.GroupName, UserName=self.user.UserName)

    def test_T3984_with_user_name_param(self):
        try:
            self.a1_r1.eim.RemoveUserFromGroup(UserName=self.user.UserName)
            known_error('TINA-4968', 'EIM/Groups Not error when remove whith one parameter')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'Missing parameter', '')

    def test_T3985_with_invalid_group_name(self):
        try:
            self.a1_r1.eim.RemoveUserFromGroup(GroupName='toto', UserName=self.user.UserName)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 404, 'NoSuchEntity', 'The group with name toto cannot be found.')

    def test_T3986_with_other_account(self):
        try:
            self.a2_r1.eim.RemoveUserFromGroup(GroupName=self.group.GroupName, UserName=self.user.UserName)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 404, 'NoSuchEntity', 'The group with name {} cannot be found.'.format(self.group.GroupName))

    def test_T4011_with_group_name(self):
        try:
            self.a1_r1.eim.RemoveUserFromGroup(GroupName=self.group.GroupName)
            known_error('TINA-4968', 'EIM/Groups Not error when remove whith one parameter')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'Missing parameter', '')
