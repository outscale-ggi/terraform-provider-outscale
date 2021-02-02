import json

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_DetachUserPolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DetachUserPolicy, cls).setup_class()
        cls.user_name = None
        cls.user = None
        cls.policy_name = None
        cls.detached = None
        try:
            cls.user_name = id_generator(prefix='user_')
            cls.user = cls.a1_r1.eim.CreateUser(UserName=cls.user_name)
            policy_document = {"Statement": [{"Sid": "full_api", "Effect": "Allow", "Action": "*", "Resource": "*"}]}
            policy_name = id_generator(prefix='policy_')
            cls.policy_arn = cls.a1_r1.eim.CreatePolicy(PolicyName=policy_name,
                                                        PolicyDocument=json.dumps(policy_document)) \
                .response.CreatePolicyResult.Policy.Arn
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception as err:
                raise err
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.user:
                if cls.policy_arn:
                    cls.a1_r1.eim.DeletePolicy(PolicyArn=cls.policy_arn)
                cls.a1_r1.eim.DeleteUser(UserName=cls.user_name)
        finally:
            super(Test_DetachUserPolicy, cls).teardown_class()

    def setup_method(self, method):
        self.detached = None
        super(Test_DetachUserPolicy, self).setup_method(method)
        try:
            self.a1_r1.eim.AttachUserPolicy(PolicyArn=self.policy_arn, UserName=self.user_name)
        except Exception as error:
            try:
                self.teardown_method(method)
            except Exception as err:
                raise err
            finally:
                raise error

    def teardown_method(self, method):
        try:
            if not self.detached:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=self.policy_arn, UserName=self.user_name)
        finally:
            super(Test_DetachUserPolicy, self).teardown_method(method)

    def test_T5514_valid_params(self):
        self.detached = self.a1_r1.eim.DetachUserPolicy(PolicyArn=self.policy_arn, UserName=self.user_name)
        ret = self.a1_r1.eim.ListAttachedUserPolicies(UserName=self.user_name).response
        assert ret.ListAttachedUserPoliciesResult.AttachedPolicies is None

    def test_T5515_no_params(self):
        try:
            self.a1_r1.eim.DetachUserPolicy()
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, "ValidationError", "Value null at 'policyArn' failed to satisfy constraint:"
                                                      " Member must not be null")

    def test_T5516_without_policy_arn(self):
        try:
            self.a1_r1.eim.DetachUserPolicy(UserName=self.user_name)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, "ValidationError", "Value null at 'policyArn' failed to satisfy constraint:"
                                                      " Member must not be null")

    def test_T5517_without_username(self):
        try:
            self.a1_r1.eim.DetachUserPolicy(PolicyArn=self.policy_arn)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            if err.message == 'The user with name None cannot be found':
                known_error('TINA-6174', 'invalid error message')
            assert False, 'Remove known error'
            assert_error(err, 404, "NoSuchEntity", "Value null at 'username' failed to satisfy constraint:"
                                                  " Member must not be null")

    def test_T5518_with_invalid_policy_arn(self):
        try:
            self.a1_r1.eim.DetachUserPolicy(PolicyArn='foo', UserName=self.user_name)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, "ValidationError", "ARN foo is not valid.")

    def test_T5519_with_invalid_username(self):
        try:
            self.a1_r1.eim.DetachUserPolicy(PolicyArn=self.policy_arn, UserName='foo')
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 404, "NoSuchEntity", "The user with name foo cannot be found")

    def test_T5520_from_another_account(self):
        try:
            self.a2_r1.eim.DetachUserPolicy(PolicyArn=self.policy_arn, UserName='foo')
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 404, "NoSuchEntity", "The user with name foo cannot be found")
