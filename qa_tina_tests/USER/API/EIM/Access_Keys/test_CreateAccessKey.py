import json
import re

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_CreateAccessKey(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateAccessKey, cls).setup_class()
        try:
            cls.username = id_generator(prefix='user_')
            cls.a1_r1.eim.CreateUser(UserName=cls.username)
            policy = {"Statement": [{"Sid": "full_api",
                                     "Effect": "Allow",
                                     "Action": "*",
                                     "Resource": "*"
                                     }]}
            cls.a1_r1.eim.PutUserPolicy(PolicyDocument=json.dumps(policy), PolicyName='full_api', UserName=cls.username)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            cls.a1_r1.eim.DeleteUserPolicy(PolicyName='full_api', UserName=cls.username)
            cls.a1_r1.eim.DeleteUser(UserName=cls.username)
        finally:
            super(Test_CreateAccessKey, cls).teardown_class()

    def test_T5451_without_param(self):
        try:
            self.a1_r1.eim.CreateAccessKey()
        except OscApiException as error:
            if error.message == "Internal Error":
                known_error("TINA-5698", "Unexpected Internal Error")

    def test_T5452_with_username(self):
        ret = None
        ak = ''
        try:
            ret = self.a1_r1.eim.CreateAccessKey(UserName=self.username).response.CreateAccessKeyResult
            ak = ret.AccessKey.AccessKeyId
            sk = ret.AccessKey.SecretAccessKey
            assert re.search(r"([A-Z0-9]{20})", ak), "AK format is not correct"
            assert re.search(r"([A-Z0-9]{40})", sk), "SK format is not correct"
            assert hasattr(ret.AccessKey, "CreateDate")
            assert ret.AccessKey.Status == "Active"
            assert ret.AccessKey.UserName == "orn:ows:idauth::{}:user/{}".format(self.a1_r1.config.account.account_id, self.username)
        finally:
            if ret:
                self.a1_r1.eim.DeleteAccessKey(UserName=self.username, AccessKeyId=ak)

    def test_T5453_with_invalid_username_type(self):
        try:
            self.a1_r1.eim.CreateAccessKey(UserName=[self.username])
        except OscApiException as err:
            # Maybe Create a Ticket for improvement of the message
            assert_error(err, 400, "ValidationError", "Invalid arguments for isAuthorized(): [arg0.resources[].relativeId: Invalid composite name part]")

    def test_T5454_with_nonexisting_username(self):
        try:
            name = 'foo'
            self.a1_r1.eim.CreateAccessKey(UserName='foo')
        except OscApiException as err:
            assert_error(err, 400, "NoSuchEntity", "The user with name cannot be found: {}".format(name))

    def test_T5455_from_another_account(self):
        try:
            self.a2_r1.eim.CreateAccessKey(UserName=self.username)
            print("isi")
        except OscApiException as err:
            assert_error(err, 400, "NoSuchEntity", "The user with name cannot be found: {}".format(self.username))
