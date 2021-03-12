from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_UpdateUser(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateUser, cls).setup_class()
        cls.user = None

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        user_name = id_generator(prefix='user_name_')
        path = '/FirstPath/'
        self.user = None
        try:
            self.user = self.a1_r1.eim.CreateUser(UserName=user_name, Path=path).response.CreateUserResult.User
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
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T3740_with_user_name_param(self):
        tmp_user_name = self.user.UserName
        tmp_user_path = self.user.Path
        self.a1_r1.eim.UpdateUser(UserName=self.user.UserName)
        assert self.user.UserName == tmp_user_name
        assert self.user.Path == tmp_user_path

    def test_T3741_with_new_path(self):
        newpath = '/SecondPath/'
        self.a1_r1.eim.UpdateUser(UserName=self.user.UserName, NewPath=newpath)
        ret = self.a1_r1.eim.GetUser(UserName=self.user.UserName)
        assert ret.response.GetUserResult.User.UserName == self.user.UserName
        assert ret.response.GetUserResult.User.Path == newpath

    def test_T3742_with_new_user_name(self):
        ret = self.a1_r1.eim.GetUser(UserName=self.user.UserName)
        assert ret.response.GetUserResult.User.UserName == self.user.UserName
        newname = id_generator(prefix='new_user_name_')
        ret = self.a1_r1.eim.UpdateUser(UserName=self.user.UserName, NewUserName=newname)
        assert ret.response.ResponseMetadata.RequestId
        ret = self.a1_r1.eim.GetUser(UserName=newname)
        assert ret.response.GetUserResult.User.UserName == newname
        self.user.UserName = newname

    def test_T3743_without_user_name(self):
        try:
            self.a1_r1.eim.UpdateUser()
            assert False, "UpdateUser must fail without UserName"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'UserName may not be empty')

    def test_T3744_with_invalid_user_name(self):
        try:
            self.a1_r1.eim.UpdateUser(UserName='totototo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 404, 'NoSuchEntity', 'Cannot find user [path=*, name=totototo] for account [arn:aws:iam::{}:account]'
                         .format(self.a1_r1.config.account.account_id))

    def test_T3745_with_invalid_new_path(self):
        invalidpathname = '/InvalidPath'
        try:
            self.a1_r1.eim.UpdateUser(UserName=self.user.UserName, NewPath=invalidpathname)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError',
                         'Path must begin and end with / and contain only alphanumeric characters and/or /_ characters')

    def test_T3746_with_invalid_new_user_name(self):
        invalidnewusername = id_generator(prefix='user_', size=66)
        try:
            self.a1_r1.eim.UpdateUser(UserName=self.user.UserName, NewUserName=invalidnewusername)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'Name size must be between 1 and 64')

    def test_T3747_with_user_name_from_other_account(self):
        try:
            self.a2_r1.eim.UpdateUser(UserName=self.user.UserName)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 404, 'NoSuchEntity', 'Cannot find user [path=*, name={}] for account [arn:aws:iam::{}:account]'
                         .format(self.user.UserName, self.a2_r1.config.account.account_id))
