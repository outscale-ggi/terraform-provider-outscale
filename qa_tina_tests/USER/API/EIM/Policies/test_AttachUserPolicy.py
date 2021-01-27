import json

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_AttachUserPolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_AttachUserPolicy, cls).setup_class()
        cls.user = None
        cls.username = None
        cls.policy_arn = None
        cls.ret = None
        try:
            cls.username = id_generator(prefix='user_')
            cls.user = cls.a1_r1.eim.CreateUser(UserName=cls.username)
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
                cls.a1_r1.eim.DeleteUser(UserName=cls.username)
        finally:
            super(Test_AttachUserPolicy, cls).teardown_class()

    def setup_method(self, method):
        super(Test_AttachUserPolicy, self).setup_method(method)
        self.policy_arn = None
        self.ret = None
        try:
            policy_document = {"Statement": [{"Sid": "full_api", "Effect": "Allow", "Action": "*", "Resource": "*"}]}
            policy_name = id_generator(prefix='policy_')
            self.policy_arn = self.a1_r1.eim.CreatePolicy(PolicyName=policy_name,
                                                          PolicyDocument=json.dumps(policy_document)) \
                .response.CreatePolicyResult.Policy.Arn
        except Exception as error:
            try:
                self.teardown_method(method)
            except Exception as err:
                raise err
            finally:
                raise error

    def teardown_method(self, method):
        try:
            if self.ret:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=self.policy_arn, UserName=self.username)
            if self.policy_arn:
                self.a1_r1.eim.DeletePolicy(PolicyArn=self.policy_arn)
        finally:
            super(Test_AttachUserPolicy, self).teardown_method(method)

    def test_T5500_valid_params(self):
        self.ret = self.a1_r1.eim.AttachUserPolicy(PolicyArn=self.policy_arn, UserName=self.username)
        assert self.ret.response.ResponseMetadata.RequestId

    def test_T5501_without_params(self):
        try:
            self.a1_r1.eim.AttachUserPolicy()
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, "ValidationError", "Value null at 'policyArn' failed to satisfy constraint:"
                                                      " Member must not be null")

    def test_T5502_without_policy_arn(self):
        try:
            self.a1_r1.eim.AttachUserPolicy(UserName=self.username)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, "ValidationError", "Value null at 'policyArn' failed to satisfy constraint:"
                                                  " Member must not be null")

    def test_T5503_without_username(self):
        try:
            self.a1_r1.eim.AttachUserPolicy(PolicyArn=self.policy_arn)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            if err.message == 'The user with name None cannot be found':
                known_error('TINA-6174', 'invalid error message')
            assert False, 'Remove known error'
            assert_error(err, 404, "NoSuchEntity", "Value null at 'username' failed to satisfy constraint:"
                                                  " Member must not be null")

    def test_T5504_with_invalid_policy_arn(self):
        try:
            self.a1_r1.eim.AttachUserPolicy(PolicyArn='foo', UserName=self.username)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, "ValidationError", "ARN foo is not valid.")

    def test_T5505_with_invalid_username(self):
        try:
            self.a1_r1.eim.AttachUserPolicy(PolicyArn=self.policy_arn, UserName='foo')
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 404, "NoSuchEntity", "The user with name foo cannot be found")

    def test_T5506_with_multiple_policies(self):
        resp = None
        policy_document = {"Statement": [{"Sid": "full_api", "Effect": "Allow", "Action": "*", "Resource": "*"}]}
        try:
            policy_name = id_generator(prefix='policy_')
            policy_arn = self.a1_r1.eim.CreatePolicy(PolicyName=policy_name,
                                                     PolicyDocument=json.dumps(policy_document)) \
                .response.CreatePolicyResult.Policy.Arn
            self.ret = self.a1_r1.eim.AttachUserPolicy(PolicyArn=self.policy_arn, UserName=self.username)
            resp = self.a1_r1.eim.AttachUserPolicy(PolicyArn=policy_arn, UserName=self.username)
            assert resp.response.ResponseMetadata.RequestId
        finally:
            if resp:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=policy_arn, UserName=self.username)
            if policy_arn:
                self.a1_r1.eim.DeletePolicy(PolicyArn=policy_arn)

    def test_T5507_with_invalid_policy_arn_type(self):
        policy_document = {"Statement": [{"Sid": "full_api", "Effect": "Allow", "Action": "*", "Resource": "*"}]}
        try:
            policy_name = id_generator(prefix='policy_')
            policy_arn = self.a1_r1.eim.CreatePolicy(PolicyName=policy_name,
                                                     PolicyDocument=json.dumps(policy_document)) \
                .response.CreatePolicyResult.Policy.Arn
            self.ret = self.a1_r1.eim.AttachUserPolicy(PolicyArn=[self.policy_arn, policy_arn], UserName=self.username)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message == 'Internal Error' and error.status_code == 500:
                known_error('TINA-6175', 'Internal Error')
            assert False, 'Remove known error'
            assert_error(error, None, "", "")
        finally:
            if policy_arn:
                self.a1_r1.eim.DeletePolicy(PolicyArn=policy_arn)

    def test_T5508_from_another_account(self):
        try:
            self.a2_r1.eim.AttachUserPolicy(PolicyArn=self.policy_arn, UserName='foo')
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 403, "AccessDenied", "You are not authorized to attach policies outside your account.")
