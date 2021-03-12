
import json

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import known_error, OscTestSuite


class Test_DeleteGroupPolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.group_name = None
        cls.policy_name = None
        super(Test_DeleteGroupPolicy, cls).setup_class()
        try:
            cls.group_name = cls.a1_r1.eim.CreateGroup(GroupName=id_generator(prefix='group_')).response.CreateGroupResult.Group.GroupName
            cls.policy = {"Statement": [{"Sid": "TestPolicy",
                                         "Effect": "Allow",
                                         "Action": "*",
                                         "Resource": "*"
                                         }
                                        ]}
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
                cls.a1_r1.eim.DeleteGroup(GroupName=cls.group_name)
        finally:
            super(Test_DeleteGroupPolicy, cls).teardown_class()

    def setup_method(self, method):
        super(Test_DeleteGroupPolicy, self).setup_method(method)
        self.policy_name = id_generator(prefix='policy_')
        self.a1_r1.eim.PutGroupPolicy(PolicyDocument=json.dumps(self.policy), PolicyName=self.policy_name, GroupName=self.group_name)

    def teardown_method(self, method):
        if self.policy_name:
            self.a1_r1.eim.DeleteGroupPolicy(PolicyName=self.policy_name, GroupName=self.group_name)
        super(Test_DeleteGroupPolicy, self).teardown_method(method)

    def test_T1473_required_param(self):
        self.a1_r1.eim.DeleteGroupPolicy(PolicyName=self.policy_name, GroupName=self.group_name)
        self.policy_name = None

    def test_T1474_without_policy_name(self):
        try:
            self.a1_r1.eim.DeleteGroupPolicy(UserName=self.group_name)
            assert False, "DeleteGroupPolicy must fail without PolicyName"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'GroupName may not be empty')

    def test_T1475_without_group_name(self):
        try:
            self.a1_r1.eim.DeleteGroupPolicy(PolicyName=self.policy_name)
            assert False, "DeleteGroupPolicy must fail without GroupName"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'GroupName may not be empty')

    def test_T1476_invalid_policy_name(self):
        try:
            self.a1_r1.eim.DeleteGroupPolicy(PolicyName='foo', GroupName=self.group_name)
            assert False, "DeleteGroupPolicy must fail with invalid PolicyName"
        except OscApiException as error:
            assert_error(error, 404, "NoSuchEntity", "The group policy with name foo cannot be found.")

    def test_T1477_invalid_group_name(self):
        try:
            self.a1_r1.eim.DeleteGroupPolicy(PolicyName=self.policy_name, GroupName='foo')
            assert False, "DeleteGroupPolicy must fail with invalid GroupName"
        except OscApiException as error:
            assert_error(error, 404, "NoSuchEntity", "The group policy with name {} cannot be found.".format(self.policy_name))
        known_error('TINA-4046', "wrong error message")
