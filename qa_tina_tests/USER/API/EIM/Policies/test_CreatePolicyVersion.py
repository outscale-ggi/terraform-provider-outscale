import json

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_CreatePolicyVersion(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreatePolicyVersion, cls).setup_class()
        cls.policy = None
        cls.ret = None
        cls.total_policies = 1

    @classmethod
    def teardown_class(cls):
        super(Test_CreatePolicyVersion, cls).teardown_class()

    def setup_method(self, method):
        super(Test_CreatePolicyVersion, self).setup_method(method)
        self.policy = None
        self.ret = None
        self.total_policies = 1
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
            if self.ret:
                if self.ret.PolicyVersion.IsDefaultVersion == 'true':
                    self.a1_r1.eim.SetDefaultPolicyVersion(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn,
                                                           VersionId='v1')
                for i in range(self.total_policies, 1, -1):
                    self.a1_r1.eim.DeletePolicyVersion(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn,
                                                       VersionId='v{}'.format(i))
            if self.policy:
                self.a1_r1.eim.DeletePolicy(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn)
        finally:
            super(Test_CreatePolicyVersion, self).teardown_method(method)

    def test_T5521_required_params(self):
        new_policy_document = {"Statement": [{"Action": "*", "Resource": "*", "Effect": "Deny", "Sid": "full_api"}]}
        self.ret = self.a1_r1.eim.CreatePolicyVersion(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn,
                                                      PolicyDocument=json.dumps(new_policy_document))\
            .response.CreatePolicyVersionResult
        assert self.ret.PolicyVersion.CreateDate
        assert self.ret.PolicyVersion.Document == json.dumps(new_policy_document)
        assert self.ret.PolicyVersion.IsDefaultVersion == 'false'
        assert self.ret.PolicyVersion.VersionId == 'v2'
        list_policy = self.a1_r1.eim.ListPolicyVersions(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn)
        assert len(list_policy.response.ListPolicyVersionsResult.Versions) == 2
        self.total_policies += 1

    def test_T5522_valid_params(self):
        new_policy_document = {"Statement": [{"Action": "*", "Resource": "*", "Effect": "Deny", "Sid": "full_api"}]}
        self.ret = self.a1_r1.eim.CreatePolicyVersion(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn,
                                                      PolicyDocument=json.dumps(new_policy_document),
                                                      SetAsDefault=True).response.CreatePolicyVersionResult
        assert self.ret.PolicyVersion.CreateDate
        assert self.ret.PolicyVersion.Document == json.dumps(new_policy_document)
        assert self.ret.PolicyVersion.IsDefaultVersion == 'true'
        assert self.ret.PolicyVersion.VersionId == 'v2'
        list_policy = self.a1_r1.eim.ListPolicyVersions(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn)
        assert len(list_policy.response.ListPolicyVersionsResult.Versions) == 2
        self.total_policies += 1

    def test_T5523_more_five_versions(self):
        try:
            for _ in range(5):
                policy_document = {"Statement": [{"Action": "*", "Resource": "*", "Effect": "Deny", "Sid": "full_api"}]}
                self.ret = self.a1_r1.eim.CreatePolicyVersion(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn,
                                                              PolicyDocument=json.dumps(policy_document))\
                    .response.CreatePolicyVersionResult
                self.total_policies += 1
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message == 'Internal Error' and error.status_code == 500:
                known_error('TINA-6203', 'eim.CreatePolicyVersion issues')
            assert False, 'Remove known error'
            assert_error(error, None, "", "")

    def test_T5524_without_policy_arn(self):
        try:
            new_policy_document = {"Statement": [{"Action": "*", "Resource": "*", "Effect": "Deny", "Sid": "full_api"}]}
            self.ret = self.a1_r1.eim.CreatePolicyVersion(PolicyDocument=json.dumps(new_policy_document)) \
                .response.CreatePolicyVersionResult
            assert False, "Call should not have been successful"
        except OscApiException as error:
            if error.message == "ARN None is not valid.":
                known_error('TINA-6203', 'eim.CreatePolicyVersion issues')
            assert False, 'Remove known error'
            assert_error(error, 400, "ValidationError", "ARN None is not valid.")

    def test_T5525_without_policy_document(self):
        try:
            self.ret = self.a1_r1.eim.CreatePolicyVersion(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn) \
                .response.CreatePolicyVersionResult
            assert False, "Call should not have been successful"
        except OscApiException as error:
            msg = "The specified value for policyDocument is invalid. It must contain only printable ASCII characters."
            if error.message == msg:
                known_error('TINA-6203', 'eim.CreatePolicyVersion issues')
            assert False, 'Remove known error'
            assert_error(error, 400, "", "")

    def test_T5526_with_invalid_policy_arn(self):
        try:
            new_policy_document = {"Statement": [{"Action": "*", "Resource": "*", "Effect": "Deny", "Sid": "full_api"}]}
            self.ret = self.a1_r1.eim.CreatePolicyVersion(PolicyArn='foo', PolicyDocument=json.dumps(new_policy_document)) \
                .response.CreatePolicyVersionResult
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", "ARN foo is not valid.")

    def test_T5527_with_invalid_policy_document(self):
        try:
            self.ret = self.a1_r1.eim.CreatePolicyVersion(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn,
                                                          PolicyDocument='foo') \
                .response.CreatePolicyVersionResult
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "MalformedPolicyDocument", "Invalid policy document")

    def test_T5528_with_invalid_set_as_default(self):
        try:
            new_policy_document = {"Statement": [{"Action": "*", "Resource": "*", "Effect": "Deny", "Sid": "full_api"}]}
            self.ret = self.a1_r1.eim.CreatePolicyVersion(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn,
                                                          PolicyDocument=json.dumps(new_policy_document),
                                                          SetAsDefault='foo').response.CreatePolicyVersionResult
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "MalformedInput", "SetAsDefault must be a boolean")

    def test_T5529_from_another_account(self):
        new_policy_document = {"Statement": [{"Action": "*", "Resource": "*", "Effect": "Deny", "Sid": "full_api"}]}
        try:
            self.ret = self.a2_r1.eim.CreatePolicyVersion(PolicyArn=self.policy.CreatePolicyResult.Policy.Arn,
                                                          PolicyDocument=json.dumps(new_policy_document)) \
                .response.CreatePolicyVersionResult
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, "InvalidInput", "ARN {} is not valid"
                         .format(self.policy.CreatePolicyResult.Policy.Arn))
