from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_sdk_pub.osc_api import AuthMethod
from time import sleep
from qa_sdk_pub import osc_api


class Test_DeleteAccessKey(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'accesskey_limit': 10}
        super(Test_DeleteAccessKey, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteAccessKey, cls).teardown_class()

    def test_T345_without_param(self):
        sleep(30)
        try:
            self.a1_r1.icu.DeleteAccessKey()
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'IcuClientException', 'Field AccessKeyId is required')

    def test_T346_with_param_but_empty(self):
        sleep(30)
        try:
            self.a1_r1.icu.DeleteAccessKey(AccessKeyId='')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: AccessKeyId')

    def test_T1799_empty_param_with_more_than_one_existing(self):
        sleep(30)
        ret_create = None
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            self.a1_r1.icu.DeleteAccessKey(AccessKeyId='')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: AccessKeyId')
        finally:
            if ret_create:
                sleep(30)
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T347_invalid_accesskeyid_foo(self):
        sleep(30)
        try:
            self.a1_r1.icu.DeleteAccessKey(AccessKeyId='foo')
            assert False, "Exception should have been raised"
        except OscApiException as error:
            assert_error(error, 400, 'NoSuchEntity', None)

    def test_T348_invalid_accesskeyid_validAK_not_existant(self):
        sleep(30)
        try:
            ak = id_generator(size=20)
            self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)
            assert False, "Exception should have been raised"
        except OscApiException as error:
            assert_error(error, 400, 'NoSuchEntity', None)

    def test_T349_invalid_accesskeyid_AK_partially_existant(self):
        sleep(30)
        ret_create = None
        ret_delete = None
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            ak_modified = "AAAA" + ak
            ret_delete = self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak_modified)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'NoSuchEntity', None)
        finally:
            if ret_create and not ret_delete:
                sleep(30)
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T350_valid_accesskeyid(self):
        sleep(30)
        ret_create = None
        ret_delete = None
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            ret_delete = self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)
            assert ret_delete.response
        finally:
            if ret_create and not ret_delete:
                sleep(30)
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T3973_method_authAkSk(self):
        sleep(30)
        ret_create = None
        ret_delete = None
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            ret_delete = self.a1_r1.icu.DeleteAccessKey(auth=AuthMethod.AkSk, AccessKeyId=ak)
            assert ret_delete.response
        finally:
            if ret_create and not ret_delete:
                sleep(30)
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T3974_with_method_authLoginPassword(self):
        sleep(30)
        ret_create = None
        ret_delete = None
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            ret_delete = self.a1_r1.icu.DeleteAccessKey(auth=AuthMethod.LoginPassword, AccessKeyId=ak)
            assert ret_delete.response
        finally:
            if ret_create and not ret_delete:
                sleep(30)
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T351_valid_accesskeyid_other_account(self):
        sleep(30)
        ret_create = None
        ret_delete = None
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            ret_delete = self.a2_r1.icu.DeleteAccessKey(AccessKeyId=ak)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'NoSuchEntity', None)
        finally:
            if ret_create and not ret_delete:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T3773_check_throttling(self):
        found_error = False
        key_id_list = []
        key_id_not_deleted_list = []
        osc_api.disable_throttling()
        for _ in range(4):
            sleep(30)
            key_id_list.append(self.a1_r1.icu.CreateAccessKey().response.accessKey.accessKeyId)
        for key_id in key_id_list:
            try:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=key_id, max_retry=0)
            except OscApiException as error:
                if error.status_code == 503:
                    found_error = True
                    key_id_not_deleted_list.append(key_id)
                else:
                    raise error
        osc_api.enable_throttling()
        for key_id in key_id_not_deleted_list:
            sleep(30)
            self.a1_r1.icu.DeleteAccessKey(AccessKeyId=key_id)
        assert found_error, "Throttling did not happen"
