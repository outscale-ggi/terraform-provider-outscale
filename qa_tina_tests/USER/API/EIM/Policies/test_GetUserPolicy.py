# pylint: disable=missing-docstring
import json
import urllib.parse

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import known_error, OscTestSuite


class Test_GetUserPolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.user_name = None
        cls.ret_pol = None
        super(Test_GetUserPolicy, cls).setup_class()
        try:
            cls.user_name = cls.a1_r1.eim.CreateUser(UserName=id_generator(prefix='user_')).response.CreateUserResult.User.UserName
            cls.policy = {"Statement": [{"Sid": "TestPolicy",
                                         "Effect": "Allow",
                                         "Action": "*",
                                         "Resource": "*"
                                         }
                                        ]
                          }
            cls.policy_name = id_generator(prefix='policy_')
            cls.ret_pol = cls.a1_r1.eim.PutUserPolicy(PolicyDocument=json.dumps(cls.policy), PolicyName=cls.policy_name,
                                                      UserName=cls.user_name)
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret_pol:
                cls.a1_r1.eim.DeleteUserPolicy(PolicyName=cls.policy_name, UserName=cls.user_name)
            if cls.user_name:
                cls.a1_r1.eim.DeleteUser(UserName=cls.user_name)
        finally:
            super(Test_GetUserPolicy, cls).teardown_class()

    def test_T1440_required_param(self):
        ret = self.a1_r1.eim.GetUserPolicy(PolicyName=self.policy_name, UserName=self.user_name)
        assert ret.response.GetUserPolicyResult.UserName == self.user_name
        assert ret.response.GetUserPolicyResult.PolicyName == self.policy_name
        assert json.loads(urllib.parse.unquote(ret.response.GetUserPolicyResult.PolicyDocument))['Statement'] == self.policy['Statement']

    def test_T1441_without_user_name(self):
        try:
            self.a1_r1.eim.GetUserPolicy(PolicyName=self.policy_name)
            assert False, "GetUserPolicy must fail without UserName"
        except OscApiException as error:
            assert_error(error, 404, "NoSuchEntity", "The user with name None cannot be found")
        known_error("TINA-4046", "Wrong error message")

    def test_T1442_without_policy_name(self):
        try:
            self.a1_r1.eim.GetUserPolicy(UserName=self.user_name)
            assert False, "GetUserPolicy must fail without PolicyName"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'PolicyName may not be empty')

    def test_T1443_invalid_policy_name(self):
        try:
            self.a1_r1.eim.GetUserPolicy(PolicyName='foo', UserName=self.user_name)
            assert False, "GetUserPolicy must fail with not existing PolicyName"
        except OscApiException as error:
            assert_error(error, 404, "NoSuchEntity", "The user policy with name foo cannot be found.")

    def test_T1444_invalid_user_name(self):
        try:
            self.a1_r1.eim.GetUserPolicy(PolicyName=self.policy_name, UserName='foo')
            assert False, "GetUserPolicy must fail with not existing UserName"
        except OscApiException as error:
            assert_error(error, 404, "NoSuchEntity", "The user with name foo cannot be found")
