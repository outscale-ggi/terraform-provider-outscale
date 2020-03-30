# pylint: disable=missing-docstring
import json
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import known_error, OscTestSuite


class Test_PutGroupPolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.group_name = None
        super(Test_PutGroupPolicy, cls).setup_class()
        try:
            cls.group_name = cls.a1_r1.eim.CreateGroup(GroupName=id_generator(prefix='group_')).response.CreateGroupResult.Group.GroupName
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
            if cls.group_name:
                for policy_name in cls.policy_list:
                    cls.a1_r1.eim.DeleteGroupPolicy(PolicyName=policy_name, GroupName=cls.group_name)
                    cls.a1_r1.eim.DeleteGroup(GroupName=cls.group_name)
        finally:
            super(Test_PutGroupPolicy, cls).teardown_class()

    def test_T1466_required_param(self):
        policy_name = id_generator(prefix='policy_')
        self.a1_r1.eim.PutGroupPolicy(PolicyDocument=json.dumps(self.policy), PolicyName=policy_name,
                                      GroupName=self.group_name)
        self.policy_list.append(policy_name)

    def test_T1468_without_policy_name(self):
        try:
            self.a1_r1.eim.PutGroupPolicy(PolicyDocument=json.dumps(self.policy), GroupName=self.group_name)
            assert False, "PutGroupPolicy must fail without PolicyName"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'PolicyName may not be empty')

    def test_T1467_without_group_name(self):
        try:
            policy_name = id_generator(prefix='policy_')
            self.a1_r1.eim.PutGroupPolicy(PolicyDocument=json.dumps(self.policy), PolicyName=policy_name)
            assert False, "PutGroupPolicy must fail without UserName"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'GroupName may not be empty')

    def test_T1469_without_policy_document(self):
        try:
            policy_name = id_generator(prefix='policy_')
            self.a1_r1.eim.PutGroupPolicy(PolicyName=policy_name, GroupName=self.group_name)
            assert False, "PutGroupPolicy must fail without PolicyDocument"
        except OscApiException as error:
            assert_error(error, 400, "ValidationError",
                         "The specified value for policyDocument is invalid. It must contain only printable ASCII characters.")
        known_error("TINA-4046", "Wrong error message")

    def test_T1470_invalid_group_name(self):
        try:
            policy_name = id_generator(prefix='policy_')
            self.a1_r1.eim.PutGroupPolicy(PolicyDocument=json.dumps(self.policy), PolicyName=policy_name,
                                          GroupName='foo')
            assert False, "PutGroupPolicy must fail with invalid UserName"
        except OscApiException as error:
            assert_error(error, 404, "NoSuchEntity", "The group with name foo cannot be found.")

    def test_T1471_invalid_policy_name(self):
        try:
            policy_name = id_generator(prefix='policy_', size=122)
            self.a1_r1.eim.PutGroupPolicy(PolicyDocument=json.dumps(self.policy), PolicyName=policy_name,
                                          GroupName=self.group_name)
            assert False, "PutGroupPolicy must fail with invalid PolicyName"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'Name size must be between 1 and 128')
            # TODO: Add tests ?

    def test_T1472_invalid_policy_document(self):
        try:
            policy_name = id_generator(prefix='policy_')
            self.a1_r1.eim.PutGroupPolicy(PolicyDocument='foo', PolicyName=policy_name, GroupName=self.group_name)
            assert False, "PutUserPolicy must fail witt invalid PolicyDocument"
        except OscApiException as error:
            assert_error(error, 400, "MalformedPolicyDocument", "Invalid policy document")
            # TODO: Add tests
