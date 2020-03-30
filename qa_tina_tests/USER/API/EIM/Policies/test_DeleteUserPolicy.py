import json

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.test_base import known_error


class Test_DeleteUserPolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.user_name = None
        super(Test_DeleteUserPolicy, cls).setup_class()
        try:
            cls.user_name = cls.a1_r1.eim.CreateUser(UserName=id_generator(prefix='user_')).response.CreateUserResult.User.UserName
            cls.policy = {"Statement": [{"Sid": "TestPolicy",
                                         "Effect": "Allow",
                                         "Action": "*",
                                         "Resource": "*"
                                         }
                                        ]
                          }
            cls.policy_name = None
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.user_name:
                cls.a1_r1.eim.DeleteUser(UserName=cls.user_name)
        finally:
            super(Test_DeleteUserPolicy, cls).teardown_class()

    def setup_method(self, method):
        super(Test_DeleteUserPolicy, self).setup_method(method)
        self.policy_name = id_generator(prefix='policy_')
        self.a1_r1.eim.PutUserPolicy(PolicyDocument=json.dumps(self.policy), PolicyName=self.policy_name, UserName=self.user_name)

    def teardown_method(self, method):
        if self.policy_name:
            self.a1_r1.eim.DeleteUserPolicy(PolicyName=self.policy_name, UserName=self.user_name)
        super(Test_DeleteUserPolicy, self).teardown_method(method)

    def test_T1435_required_param(self):
        self.a1_r1.eim.DeleteUserPolicy(PolicyName=self.policy_name, UserName=self.user_name)
        self.policy_name = None

    def test_T1436_without_policy_name(self):
        try:
            self.a1_r1.eim.DeleteUserPolicy(UserName=self.user_name)
            assert False, "DeleteUserPolicy must fail without PolicyName"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'PolicyName may not be empty')

    def test_T1437_without_user_name(self):
        try:
            self.a1_r1.eim.DeleteUserPolicy(PolicyName=self.policy_name)
            assert False, "DeleteUserPolicy must fail without UserName"
        except OscApiException as error:
            assert_error(error, 404, "NoSuchEntity", "The user with name None cannot be found.")
        known_error("TINA-4046", "Wrong error message")

    def test_T1438_invalid_policy_name(self):
        try:
            self.a1_r1.eim.DeleteUserPolicy(PolicyName='foo', UserName=self.user_name)
            assert False, "DeleteUserPolicy must fail with invalid PolicyName"
        except OscApiException as error:
            assert_error(error, 404, "NoSuchEntity", "Cannot find permission policy [name=foo, level=USER] " \
                         +"for entity [arn:aws:iam::{}:user/{}]".format(self.a1_r1.config.account.account_id, self.user_name))
        known_error("TINA-4046", "Wrong error message")

    def test_T1439_invalid_user_name(self):
        try:
            self.a1_r1.eim.DeleteUserPolicy(PolicyName=self.policy_name, UserName='foo')
            assert False, "DeleteUserPolicy must fail with invalid UserName"
        except OscApiException as error:
            assert_error(error, 404, "NoSuchEntity", "The user with name foo cannot be found.")
