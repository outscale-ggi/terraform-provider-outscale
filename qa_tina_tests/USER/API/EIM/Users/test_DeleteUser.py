
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_DeleteUser(OscTestSuite):

    def test_T1432_required_param(self):
        ret = self.a1_r1.eim.CreateUser(UserName=id_generator(prefix='user_'))
        self.a1_r1.eim.DeleteUser(UserName=ret.response.CreateUserResult.User.UserName)

    def test_T1433_without_user_name(self):
        try:
            self.a1_r1.eim.DeleteUser()
            assert False, "DeleteUser must fail without UserName"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'UserName may not be empty')

    def test_T1434_invalid_user_name(self):
        try:
            self.a1_r1.eim.DeleteUser(UserName='foo')
            assert False, "DeleteUser must fail with not existing UserName"
        except OscApiException as error:
            assert_error(error, 404, "NoSuchEntity", "The User with name foo cannot be found")

    def test_T3677_with_user_name_from_other_account(self):
        user_name = id_generator(prefix='user_')
        self.a1_r1.eim.CreateUser(UserName=user_name)
        try:
            self.a2_r1.eim.DeleteUser(UserName=user_name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 404, 'NoSuchEntity', "The User with name {} cannot be found".format(user_name))
        finally:
            self.a1_r1.eim.DeleteUser(UserName=user_name)
