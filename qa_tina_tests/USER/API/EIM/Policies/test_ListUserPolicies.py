import json

from qa_sdk_common.exceptions import OscApiException
from qa_sdks import OscSdk
from qa_test_tools.config import OscConfig
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_ListUserPolicies(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ListUserPolicies, cls).setup_class()
        cls.user_name = None
        cls.user = None
        cls.policy_name = None
        cls.attached = None
        cls.create_ak = None
        cls.conn_user = None
        try:
            cls.user_name = id_generator(prefix='user_')
            cls.user = cls.a1_r1.eim.CreateUser(UserName=cls.user_name)
            policy_document = {"Statement": [{"Sid": "full_api", "Effect": "Allow", "Action": "*", "Resource": "*"}]}
            cls.policy_name = id_generator(prefix='policy_')
            cls.attached = cls.a1_r1.eim.PutUserPolicy(PolicyDocument=json.dumps(policy_document),
                                                       PolicyName=cls.policy_name, UserName=cls.user_name)
            cls.create_ak = cls.a1_r1.eim.CreateAccessKey(UserName=cls.user_name)
            cls.conn_user = OscSdk(config=OscConfig.get_with_keys(az_name=cls.a1_r1.config.region.az_name,
                                                                  ak=cls.create_ak.response.CreateAccessKeyResult.AccessKey.AccessKeyId,
                                                                  sk=cls.create_ak.response.CreateAccessKeyResult.AccessKey.SecretAccessKey))
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception as err:
                raise err
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        super(Test_ListUserPolicies, cls).teardown_class()
        if cls.user:
            if cls.attached:
                cls.a1_r1.eim.DeleteUserPolicy(PolicyName=cls.policy_name, UserName=cls.user_name)
            if cls.create_ak:
                cls.a1_r1.eim.DeleteAccessKey(UserName=cls.user_name,
                                              AccessKeyId=cls.create_ak.response.CreateAccessKeyResult.AccessKey.AccessKeyId)
            cls.a1_r1.eim.DeleteUser(UserName=cls.user_name)

    def test_T5509_valid_params(self):
        ret = self.a1_r1.eim.ListUserPolicies(UserName=self.user_name)
        assert len(ret.response.ListUserPoliciesResult.PolicyNames) == 1
        assert ret.response.ListUserPoliciesResult.PolicyNames[0] == self.policy_name

    def test_T5510_without_params(self):
        try:
            self.a1_r1.eim.ListUserPolicies()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message == 'The user with name None cannot be found':
                known_error('TINA-6195', 'incorrect error message')
            assert False, 'Remove known error'
            assert_error(error, 404, "NoSuchEntity", "")

    def test_T5511_with_invalid_username(self):
        try:
            self.a1_r1.eim.ListUserPolicies(UserName='toto')
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, "NoSuchEntity", "The user with name toto cannot be found")

    def test_T5512_with_invalid_username_type(self):
        try:
            self.a1_r1.eim.ListUserPolicies(UserName=[self.user_name])
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, "ValidationError", "Invalid arguments for isAuthorized():"
                                                   " [arg0.resources[].relativeId: Invalid composite name part]")

    def test_T5513_from_another_account(self):
        try:
            self.a2_r1.eim.ListUserPolicies(UserName=self.user_name)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, "NoSuchEntity", "The user with name {} cannot be found".format(self.user_name))
