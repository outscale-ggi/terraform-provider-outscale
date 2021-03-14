from datetime import datetime

from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite


NUM_USERS = 3


class Test_ListUsers(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ListUsers, cls).setup_class()
        cls.user_list = []
        # cls.pfx = id_generator(size=4)
        # cls.username = id_generator(prefix='user_')
        try:
            for _ in range(NUM_USERS):
                pfx = id_generator(size=4)
                username = id_generator(prefix='user_')
                cls.user_list.append(cls.a1_r1.eim.CreateUser(UserName=username,
                                                              Path='/pfx/{}/'.format(pfx)).response.CreateUserResult.User)

        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            for user in cls.user_list:
                cls.a1_r1.eim.DeleteUser(UserName=user.UserName)
        finally:
            super(Test_ListUsers, cls).teardown_class()

    def test_T3702_without_params(self):
        ret = self.a1_r1.eim.ListUsers()
        assert len(ret.response.ListUsersResult.Users) == NUM_USERS
        for user in ret.response.ListUsersResult.Users:
            assert user.Arn.startswith('arn:aws:iam::{}:user/pfx/'.format(self.a1_r1.config.account.account_id))
            assert datetime.strptime(user.CreateDate, '%Y-%m-%dT%H:%M:%S.%fZ')
            assert user.Path.startswith('/pfx/')
            assert user.UserId
            assert user.UserName in [usr.UserName for usr in self.user_list]

    def test_T3703_with_path_prefix(self):
        ret = self.a1_r1.eim.ListUsers(PathPrefix='/pfx/')
        assert len(ret.response.ListUsersResult.Users) == NUM_USERS
        ret = self.a1_r1.eim.ListUsers(PathPrefix=self.user_list[0].Path)
        assert len(ret.response.ListUsersResult.Users) == 1
        assert ret.response.ListUsersResult.Users[0].UserName == self.user_list[0].UserName

    def test_T3704_with_invalid_path_prefix(self):
        ret = self.a1_r1.eim.ListUsers(PathPrefix='toto/toto')
        assert not ret.response.ListUsersResult.Users

    def test_T3705_with_path_prefix_from_other_account(self):
        ret = self.a2_r1.eim.ListUsers(Path='/pfx/')
        assert not ret.response.ListUsersResult.Users, 'Unexpected non-empty result'
