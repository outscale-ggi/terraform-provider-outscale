from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_UpdateAccessKey(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateAccessKey, cls).setup_class()
        cls.user = None
        cls.ak_id = None
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
            super(Test_UpdateAccessKey, cls).teardown_class()

    def setup_method(self, method):
        super(Test_UpdateAccessKey, self).setup_method(method)
        self.ak_id = None
        try:
            ret = self.a1_r1.eim.CreateAccessKey(UserName=self.username)
            self.ak_id = ret.response.CreateAccessKeyResult.AccessKey.AccessKeyId
        except Exception as error:
            try:
                self.teardown_method(method)
            except Exception as err:
                raise err
            finally:
                raise error

    def teardown_method(self, method):
        try:
            if self.ak_id:
                self.a1_r1.eim.DeleteAccessKey(UserName=self.username, AccessKeyId=self.ak_id)
        finally:
            super(Test_UpdateAccessKey, self).teardown_method(method)

    def test_T5461_with_required_params(self):
        before_ak = self.a1_r1.eim.ListAccessKeys(UserName=self.username).response.ListAccessKeysResult
        before_creation_date = before_ak.AccessKeyMetadata[0].CreateDate
        self.a1_r1.eim.UpdateAccessKey(AccessKeyId=self.ak_id, Status='Inactive', UserName=self.username)
        ret = self.a1_r1.eim.ListAccessKeys(UserName=self.username).response.ListAccessKeysResult
        assert ret.AccessKeyMetadata[0].Status == "Inactive"
        assert ret.AccessKeyMetadata[0].CreateDate == before_creation_date

    def test_T5462_without_params(self):
        try:
            self.a1_r1.eim.UpdateAccessKey()
            assert False, "Call should not have been successful"
        except OscApiException as error:
            if error.message == "Internal Error":
                known_error("TINA-6165", "Unexpected Internal Error")
            assert False, "Remove known error"

    def test_T5463_without_username(self):
        try:
            self.a1_r1.eim.UpdateAccessKey(AccessKeyId=self.ak_id, Status='Active')
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 404, "NoSuchEntity", "Cannot find access key [pid={}] for entity [arn:aws:iam::{}:account]"
                         .format(self.ak_id, self.a1_r1.config.account.account_id))

    def test_T5464_without_accesskey_id(self):
        try:
            self.a1_r1.eim.UpdateAccessKey(Status='Inactive', UserName=self.username)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, "ValidationError", "AccessKeyId may not be empty")

    def test_T5465_without_status(self):
        try:
            self.a1_r1.eim.UpdateAccessKey(AccessKeyId=self.ak_id, UserName=self.username)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            if error.message == "Internal Error":
                known_error("TINA-6166", "Unexpected Internal Error")
            else:
                assert False, "Remove known error"
                assert_error(error, 400, "", "")

    def test_T5466_with_invalid_accesskey_id(self):
        try:
            self.a1_r1.eim.UpdateAccessKey(AccessKeyId='foo', Status='Inactive', UserName=self.username)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 404, "NoSuchEntity", "Cannot find access key [pid={}] for entity [arn:aws:iam::{}:user/{}]"
                         .format('foo', self.a1_r1.config.account.account_id, self.username))

    def test_T5467_with_invalid_status(self):
        try:
            self.a1_r1.eim.UpdateAccessKey(AccessKeyId=self.ak_id, Status='foo', Username=self.username)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, "InvalidParameterValue",
                         "Request contains an invalid parameter value \"{}\" for key \"Status\"".format('foo'.upper()))

    def test_T5468_with_invalid_username(self):
        try:
            self.a1_r1.eim.UpdateAccessKey(AccessKeyId=self.ak_id, Status='Inactive', UserName='foo')
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 404, "NoSuchEntity", "The user with name {} cannot be found.".format('foo'))

    def test_T5469_from_another_account(self):
        try:
            self.a2_r1.eim.UpdateAccessKey(AccessKeyId=self.ak_id, Status='Inactive', UserName=self.username)
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 404, "NoSuchEntity", "The user with name {} cannot be found.".format(self.username))

    def test_T5499_without_username_with_ak_account(self):
        ak_id_account = None
        try:
            ak_id_account = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.eim.UpdateAccessKey(AccessKeyId=ak_id_account, Status='Inactive')
            ret = self.a1_r1.eim.ListAccessKeys().response.ListAccessKeysResult
            for meta in ret.AccessKeyMetadata:
                if meta.AccessKeyId == ak_id_account:
                    assert meta.Status == "Inactive"
        finally:
            if ak_id_account:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak_id_account)
