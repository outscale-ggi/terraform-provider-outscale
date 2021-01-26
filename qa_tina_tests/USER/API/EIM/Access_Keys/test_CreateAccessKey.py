import re

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_CreateAccessKey(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateAccessKey, cls).setup_class()
        cls.user = None
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
            super(Test_CreateAccessKey, cls).teardown_class()

    def test_T5451_without_param(self):
        ret = None
        try:
            ret = self.a1_r1.eim.CreateAccessKey().response.CreateAccessKeyResult
            assert False, "Remove known error"
            ak = ret.AccessKey.AccessKeyId
            sk = ret.AccessKey.SecretAccessKey
            assert re.search(r"([A-Z0-9]{20})", ak), "AK format is not correct"
            assert re.search(r"([A-Z0-9]{40})", sk), "SK format is not correct"
            assert hasattr(ret.AccessKey, "CreateDate")
            assert ret.AccessKey.Status == "Active"
            assert ret.AccessKey.UserName == "orn:ows:idauth::{}:account".format(self.a1_r1.config.account.account_id)
        except OscApiException as error:
            if error.message == "Internal Error":
                known_error("TINA-5698", "Unexpected Internal Error")
            assert False, "Remove known error"
        finally:
            if ret:
                self.a1_r1.eim.DeleteAccessKey(UserName=self.username, AccessKeyId=ak)

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
            assert ret.AccessKey.UserName == "orn:ows:idauth::{}:user/{}"\
                .format(self.a1_r1.config.account.account_id, self.username)
        finally:
            if ret:
                self.a1_r1.eim.DeleteAccessKey(UserName=self.username, AccessKeyId=ak)

    def test_T5453_with_invalid_username_type(self):
        try:
            self.a1_r1.eim.CreateAccessKey(UserName=[self.username])
            assert False, "Call should not have been successful"
        except OscApiException as err:
            # Maybe Create a Ticket for improvement of the message
            assert_error(err, 400, "ValidationError", "Invalid arguments for isAuthorized():"
                                                      " [arg0.resources[].relativeId: Invalid composite name part]")

    def test_T5454_with_nonexisting_username(self):
        name = 'foo'
        try:
            self.a1_r1.eim.CreateAccessKey(UserName=name)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, "NoSuchEntity", "The user with name cannot be found: {}".format(name))

    def test_T5455_from_another_account(self):
        try:
            self.a2_r1.eim.CreateAccessKey(UserName=self.username)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, "NoSuchEntity", "The user with name cannot be found: {}".format(self.username))
