import json

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_DeletePolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeletePolicy, cls).setup_class()
        cls.policy = None
        cls.deleted = None

    def setup_method(self, method):
        super(Test_DeletePolicy, self).setup_method(method)
        self.policy = None
        self.deleted = None
        try:
            policy_document = {"Statement": [{"Sid": "full_api", "Effect": "Allow", "Action": "*", "Resource": "*"}]}
            policy_name = id_generator(prefix='policy_')
            self.policy = self.a1_r1.eim.CreatePolicy(PolicyName=policy_name,
                                                      PolicyDocument=json.dumps(policy_document)).response
        except Exception as error:
            try:
                self.teardown_method(method)
            except Exception as err:
                raise err
            finally:
                raise error

    def teardown_method(self, method):
        try:
            if not self.deleted:
                self.a1_r1.eim.DeletePolicy(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn)
        finally:
            super(Test_DeletePolicy, self).teardown_method(method)

    def test_T5530_valid_params(self):
        self.deleted = self.a1_r1.eim.DeletePolicy(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn)

    def test_T5531_without_arn(self):
        try:
            self.a1_r1.eim.DeletePolicy()
            assert False, "Call should not have been successful"
        except OscApiException as error:
            if error.message == "ARN None is not valid.":
                known_error('TINA-6208', 'eim.DeletePolicy() issues')
            assert False, 'Remove known error and update the assert error'
            assert_error(error, 400, "", "")

    def test_T5532_with_invalid_arn(self):
        try:
            self.a1_r1.eim.DeletePolicy(PolicyArn='foo')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", "ARN foo is not valid.")

    def test_T5533_with_invalid_arn_type(self):
        try:
            self.a1_r1.eim.DeletePolicy(PolicyArn=[self.policy.CreatePolicyResult.Policy.Arn])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            if error.message == "Internal Error":
                known_error('TINA-6208', 'eim.DeletePolicy() issues')
            assert False, 'Remove known error and update the assert error'
            assert_error(error, 400, "", "")

    def test_T5534_from_another_account(self):
        try:
            self.a2_r1.eim.DeletePolicy(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 403, "AccessDenied", "You are not authorized to delete policies outside your account.")
