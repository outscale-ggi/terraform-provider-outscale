import re

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_tina_tools.test_base import OscTinaTest


NB_ACCESSKEY = 2


class Test_ListAccessKeys(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_ListAccessKeys, cls).setup_class()
        cls.ret_create = None
        try:
            cls.username = id_generator(prefix='user_')
            cls.ret_create = cls.a1_r1.eim.CreateUser(UserName=cls.username)
            for _ in range(NB_ACCESSKEY):
                cls.a1_r1.eim.CreateAccessKey(UserName=cls.username)
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
            if cls.ret_create:
                ret = cls.a1_r1.eim.ListAccessKeys(UserName=cls.username)
                for key in ret.response.ListAccessKeysResult.AccessKeyMetadata:
                    cls.a1_r1.eim.DeleteAccessKey(UserName=cls.username, AccessKeyId=key.AccessKeyId)
                cls.a1_r1.eim.DeleteUser(UserName=cls.username)
        finally:
            super(Test_ListAccessKeys, cls).teardown_class()

    def test_T5470_no_params(self):
        ret = self.a1_r1.eim.ListAccessKeys().response.ListAccessKeysResult
        assert len(ret.AccessKeyMetadata) >= 1
        for ak in ret.AccessKeyMetadata:
            assert re.search(r"([A-Z0-9]{20})", ak.AccessKeyId), "AK format is not correct"
            assert hasattr(ak, "CreateDate")
            assert getattr(ak, "Status") in ["Active", "Inactive"]

    def test_T5471_with_username(self):
        ret = self.a1_r1.eim.ListAccessKeys(UserName=self.username).response.ListAccessKeysResult
        assert len(ret.AccessKeyMetadata) == NB_ACCESSKEY
        for ak in ret.AccessKeyMetadata:
            assert ak.UserName == self.username
            assert re.search(r"([A-Z0-9]{20})", ak.AccessKeyId), "AK format is not correct"
            assert hasattr(ak, "CreateDate")
            assert ak.Status == "Active"

    def test_T5472_with_invalid_username_type(self):
        try:
            self.a1_r1.eim.ListAccessKeys(UserName=[self.username])
            assert False, "Call should not have been successful"
        except OscApiException as err:
            # Maybe Create a Ticket for improvement of the message
            assert_error(err, 400, "ValidationError", "Invalid arguments for isAuthorized(): "
                                                    "[arg0.resources[].relativeId: Invalid composite name part]")

    def test_T5473_with_nonexisting_username(self):
        name = 'foo'
        try:
            self.a1_r1.eim.ListAccessKeys(UserName=name)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 404, "NoSuchEntity", "The user with name {} cannot be found.".format(name))

    def test_T5474_from_another_account(self):
        try:
            self.a2_r1.eim.ListAccessKeys(UserName=self.username)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 404, "NoSuchEntity", "The user with name {} cannot be found.".format(self.username))
