

import json

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_DeleteAccessKey(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteAccessKey, cls).setup_class()
        try:
            cls.username = id_generator(prefix='user_')
            cls.a1_r1.eim.CreateUser(UserName=cls.username)
            policy = {"Statement": [{"Sid": "full_api",
                                     "Effect": "Allow",
                                     "Action": "*",
                                     "Resource": "*"
                                     }]}
            cls.a1_r1.eim.PutUserPolicy(PolicyDocument=json.dumps(policy), PolicyName='full_api', UserName=cls.username)
            ret = cls.a1_r1.eim.CreateAccessKey(UserName=cls.username)
            cls.conn_user = OscSdk(config=OscConfig.get_with_keys(az_name=cls.a1_r1.config.region.az_name,
                                                                  ak=ret.response.CreateAccessKeyResult.AccessKey.AccessKeyId,
                                                                  sk=ret.response.CreateAccessKeyResult.AccessKey.SecretAccessKey))
            cls.tested_ak = None
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
            ret = cls.a1_r1.eim.ListAccessKeys(UserName=cls.username)
            for key in ret.response.ListAccessKeysResult.AccessKeyMetadata:
                ret = cls.a1_r1.eim.DeleteAccessKey(UserName=cls.username, AccessKeyId=key.AccessKeyId)
            cls.a1_r1.eim.DeleteUserPolicy(PolicyName='full_api', UserName=cls.username)
            ret = cls.a1_r1.eim.DeleteUser(UserName=cls.username)
        finally:
            super(Test_DeleteAccessKey, cls).teardown_class()

    def setup_method(self, method):
        super(Test_DeleteAccessKey, self).setup_method(method)
        try:
            ret = self.a1_r1.eim.CreateAccessKey(UserName=self.username)
            self.tested_ak = ret.response.CreateAccessKeyResult.AccessKey.AccessKeyId
        except Exception as error:
            try:
                self.teardown_method(method)
            except Exception as err:
                raise err
            finally:
                raise error

    def teardown_method(self, method):
        try:
            if self.tested_ak:
                self.a1_r1.eim.DeleteAccessKey(UserName=self.username, AccessKeyId=self.tested_ak)
        finally:
            super(Test_DeleteAccessKey, self).teardown_method(method)

    def test_T1671_required_param(self):
        self.conn_user.eim.DeleteAccessKey(AccessKeyId=self.tested_ak)
        self.tested_ak = None

    def test_T1672_without_access_key_id(self):
        try:
            self.conn_user.eim.DeleteAccessKey()
            assert False
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'AccessKeyId may not be empty')

    def test_T1673_with_invalid_access_key_id(self):
        try:
            self.conn_user.eim.DeleteAccessKey(AccessKeyId='foo')
            assert False
        except OscApiException as error:
            assert_error(error, 404, "NoSuchEntity",
                         "Cannot find access key [pid=foo] for entity [arn:aws:iam::{}:user/{}]".format(self.a1_r1.config.account.account_id, \
                                                                                                        self.username))

    def test_T1675_with_user_name(self):
        self.a1_r1.eim.DeleteAccessKey(AccessKeyId=self.tested_ak, UserName=self.username)
        self.tested_ak = None

    def test_T1674_with_invalid_user_name(self):
        try:
            self.a1_r1.eim.DeleteAccessKey(AccessKeyId=self.tested_ak, UserName='foo')
            assert False
        except OscApiException as error:
            assert_error(error, 400, "NoSuchEntity", "UnknownPrincipalException")
