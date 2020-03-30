import json
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.test_base import known_error
import urllib.parse


class Test_GetGroupPolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.group_name = None
        cls.ret_pol = None
        super(Test_GetGroupPolicy, cls).setup_class()
        try:
            cls.group_name = cls.a1_r1.eim.CreateGroup(GroupName=id_generator(prefix='group_')).response.CreateGroupResult.Group.GroupName
            cls.policy = {"Statement": [{"Sid": "TestPolicy",
                                         "Effect": "Allow",
                                         "Action": "*",
                                         "Resource": "*"
                                         }
                                        ]}
            cls.policy_name = id_generator(prefix='policy_')
            cls.ret_pol = cls.a1_r1.eim.PutGroupPolicy(PolicyDocument=json.dumps(cls.policy), PolicyName=cls.policy_name,
                                                       GroupName=cls.group_name)
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
                cls.a1_r1.eim.DeleteGroupPolicy(PolicyName=cls.policy_name, GroupName=cls.group_name)
            if cls.group_name:
                cls.a1_r1.eim.DeleteGroup(GroupName=cls.group_name)
        finally:
            super(Test_GetGroupPolicy, cls).teardown_class()

    def test_T1478_required_param(self):
        ret = self.a1_r1.eim.GetGroupPolicy(PolicyName=self.policy_name, GroupName=self.group_name)
        assert ret.response.GetGroupPolicyResult.GroupName == self.group_name
        assert ret.response.GetGroupPolicyResult.PolicyName == self.policy_name
        assert json.loads(urllib.parse.unquote(ret.response.GetGroupPolicyResult.PolicyDocument))['Statement'] == self.policy['Statement']

    def test_T1479_without_group_name(self):
        try:
            self.a1_r1.eim.GetGroupPolicy(PolicyName=self.policy_name)
            assert False, "GetGroupPolicy must fail without GroupName"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'GroupName may not be empty')

    def test_T1480_without_policy_name(self):
        try:
            self.a1_r1.eim.GetGroupPolicy(GroupName=self.group_name)
            assert False, "GetGroupPolicy must fail without PolicyName"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'PolicyName may not be empty')

    def test_T1481_invalid_policy_name(self):
        try:
            self.a1_r1.eim.GetGroupPolicy(PolicyName='foo', GroupName=self.group_name)
            assert False, "GetGroupPolicy must fail with not existing PolicyName"
        except OscApiException as error:
            assert_error(error, 404, "NoSuchEntity", "The group policy with name foo cannot be found.")

    def test_T1482_invalid_group_name(self):
        try:
            self.a1_r1.eim.GetGroupPolicy(PolicyName=self.policy_name, GroupName='foo')
            assert False, "GetGroupPolicy must fail with not existing GroupName"
        except OscApiException as error:
            assert_error(error, 404, "NoSuchEntity", "The group policy with name {} cannot be found.".format(self.policy_name))
        known_error('TINA-4046', "wrong error message")
