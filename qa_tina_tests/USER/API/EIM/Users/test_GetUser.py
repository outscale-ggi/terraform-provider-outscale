from datetime import datetime

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_GetUser(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.user = None
        cls.user_name = id_generator(prefix='user_')
        super(Test_GetUser, cls).setup_class()
        try:
            cls.user = cls.a1_r1.eim.CreateUser(UserName=cls.user_name)
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
                cls.a1_r1.eim.DeleteUser(UserName=cls.user_name)
        finally:
            super(Test_GetUser, cls).teardown_class()

    def test_T3678_with_invalid_user_name(self):
        try:
            self.a1_r1.eim.GetUser(UserName='titi')
            assert False, 'GetUser must fail with invalid UserName'
        except OscApiException as error:
            assert_error(error, 404, 'NoSuchEntity', 'The User with name titi cannot be found')

    def test_T3688_with_user_name_from_other_account(self):
        try:
            self.a2_r1.eim.GetUser(UserName=self.user_name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 404, 'NoSuchEntity', "The User with name {} cannot be found".format(self.user_name))

    def test_T3689_with_user_name(self):
        ret = self.a1_r1.eim.GetUser(UserName=self.user_name)
        assert ret.response.GetUserResult.User.Arn == 'arn:aws:iam::{}:user/{}'.format(self.a1_r1.config.account.account_id,
                                                                                       self.user_name)
        assert datetime.strptime(ret.response.GetUserResult.User.CreateDate, '%Y-%m-%dT%H:%M:%S.%fZ')
        assert ret.response.GetUserResult.User.Path == '/'
        assert ret.response.GetUserResult.User.UserId
        assert ret.response.GetUserResult.User.UserName == self.user_name

    def test_T3701_without_params(self):
        ret = self.a1_r1.eim.GetUser()
        assert ret.response.GetUserResult.User.UserId == self.a1_r1.config.account.account_id
        assert ret.response.GetUserResult.User.Arn == 'arn:aws:iam::{}:account'.format(self.a1_r1.config.account.account_id)
        assert datetime.strptime(ret.response.GetUserResult.User.CreateDate, '%Y-%m-%dT%H:%M:%S.%fZ')
        assert ret.response.GetUserResult.User.Path == '/'
        assert ret.response.GetUserResult.User.UserName.lower() == self.a1_r1.config.account.login.lower()
