import json
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import id_generator, assert_error
from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.test_base import known_error


class Test_PutUserPolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.user_name = None
        super(Test_PutUserPolicy, cls).setup_class()
        try:
            cls.user_name = cls.a1_r1.eim.CreateUser(UserName=id_generator(prefix='user_')).response.CreateUserResult.User.UserName
            cls.policy = {"Statement": [{"Sid": "TestPolicy",
                                         "Effect": "Allow",
                                         "Action": "*",
                                         "Resource": "*"
                                         }
                                        ]
                          }
            cls.policy_list = []
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
                for policy_name in cls.policy_list:
                    cls.a1_r1.eim.DeleteUserPolicy(PolicyName=policy_name, UserName=cls.user_name)
                cls.a1_r1.eim.DeleteUser(UserName=cls.user_name)
        finally:
            super(Test_PutUserPolicy, cls).teardown_class()

    def test_T1445_required_param(self):
        policy_name = id_generator(prefix='policy_')
        self.a1_r1.eim.PutUserPolicy(PolicyDocument=json.dumps(self.policy), PolicyName=policy_name, UserName=self.user_name)
        self.policy_list.append(policy_name)

    def test_T1446_without_user_name(self):
        try:
            policy_name = id_generator(prefix='policy_')
            self.a1_r1.eim.PutUserPolicy(PolicyDocument=json.dumps(self.policy), PolicyName=policy_name)
            assert False, "PutUserPolicy must fail without UserName"
        except OscApiException as error:
            assert_error(error, 400, "NoSuchEntity", "The user with name None cannot be found")
        known_error("TINA-4046", "Wrong error message")

    def test_T1447_without_policy_name(self):
        try:
            self.a1_r1.eim.PutUserPolicy(PolicyDocument=json.dumps(self.policy), UserName=self.user_name)
            assert False, "PutUserPolicy must fail without PolicyName"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'PolicyName may not be empty')

    def test_T1448_without_policy_document(self):
        try:
            policy_name = id_generator(prefix='policy_')
            self.a1_r1.eim.PutUserPolicy(PolicyName=policy_name, UserName=self.user_name)
            assert False, "PutUserPolicy must fail without PolicyDocument"
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", 
                         "The specified value for policyDocument is invalid. It must contain only printable ASCII characters.")
        known_error("TINA-4046", "Wrong error message")

    def test_T1449_invalid_user_name(self):
        try:
            policy_name = id_generator(prefix='policy_')
            self.a1_r1.eim.PutUserPolicy(PolicyDocument=json.dumps(self.policy), PolicyName=policy_name, UserName='foo')
            assert False, "PutUserPolicy must fail with invali UserName"
        except OscApiException as error:
            assert_error(error, 400, "NoSuchEntity", "The user with name foo cannot be found")

    def test_T1450_invalid_policy_name(self):
        try:
            policy_name = id_generator(prefix='policy_', size=122)
            self.a1_r1.eim.PutUserPolicy(PolicyDocument=json.dumps(self.policy), PolicyName=policy_name, UserName=self.user_name)
            assert False, "PutUserPolicy must fail with invalid PolicyName"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'Name size must be between 1 and 128')
        # TODO: Add tests ?

    def test_T1451_invalid_policy_document(self):
        try:
            policy_name = id_generator(prefix='policy_')
            self.a1_r1.eim.PutUserPolicy(PolicyDocument='foo', PolicyName=policy_name, UserName=self.user_name)
            assert False, "PutUserPolicy must fail witt invalid PolicyDocument"
        except OscApiException as error:
            assert_error(error, 400, "MalformedPolicyDocument", "Invalid policy document")
        # TODO: Add tests
