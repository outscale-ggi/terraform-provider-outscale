from time import sleep
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_tina_tools.specs.oapi.check_tools import check_oapi_response
from qa_sdk_pub import osc_api
from qa_sdk_pub.osc_api import AuthMethod


class Test_DeleteAccessKey(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'accesskey_limit': 10}
        super(Test_DeleteAccessKey, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteAccessKey, cls).teardown_class()

    def test_T4817_without_param(self):
        try:
            self.a1_r1.oapi.DeleteAccessKey()
            assert False, "Call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, '7000', 'MissingParameter')

    def test_T4818_with_param_but_empty(self):
        try:
            self.a1_r1.oapi.DeleteAccessKey(AccessKeyId='')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'MissingParameter', 7000)

    def test_T4819_empty_param_with_more_than_one_existing(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            self.a1_r1.oapi.DeleteAccessKey(AccessKeyId='')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error,  400, '7000', 'MissingParameter')
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4820_invalid_accesskeyid_foo(self):
        try:
            self.a1_r1.oapi.DeleteAccessKey(AccessKeyId='foo')
            assert False, "Exception should have been raised"
        except OscApiException as error:
            misc.assert_error(error, 400, '5076', 'InvalidResource')

    def test_T4821_invalid_accesskeyid_validAK_not_existant(self):
        try:
            ak = misc.id_generator(size=20)
            self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)
            assert False, "Exception should have been raised"
        except OscApiException as error:
            misc.assert_error(error, 400, '5076', 'InvalidResource')

    def test_T4822_invalid_accesskeyid_AK_partially_existant(self):
        ret_create = None
        ret_delete = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            ak_modified = "AAAA" + ak
            ret_delete = self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak_modified)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, '5076', 'InvalidResource')
        finally:
            if ret_create and not ret_delete:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4823_valid_accesskeyid(self):
        ret_create = None
        ret_delete = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            ret_delete = self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)
            check_oapi_response(ret_delete.response, 'DeleteAccessKeyResponse')
        finally:
            if ret_create and not ret_delete:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4824_with_method_authLoginPassword(self):
        ret_create = None
        ret_delete = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            ret_delete = self.a1_r1.oapi.DeleteAccessKey(auth=AuthMethod.LoginPassword, AccessKeyId=ak)
            assert False, 'remove known error'
            check_oapi_response(ret_delete.response, 'DeleteAccessKeyResponse')
        except Exception as error:
            known_error('GTW-1240', 'SDK implementation ')
        finally:
            if ret_create and not ret_delete:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4825_valid_accesskeyid_other_account(self):
        ret_create = None
        ret_delete = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            ret_delete = self.a2_r1.oapi.DeleteAccessKey(AccessKeyId=ak)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, '5076', 'InvalidResource')
        finally:
            if ret_create and not ret_delete:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4826_check_throttling(self):
        found_error = False
        key_id_list = []
        key_id_not_deleted_list = []
        osc_api.disable_throttling()
        for _ in range(4):
            key_id_list.append(self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId)
        for key_id in key_id_list:
            try:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=key_id, max_retry=0)
            except OscApiException as error:
                if error.status_code == 503:
                    found_error = True
                    key_id_not_deleted_list.append(key_id)
                else:
                    raise error
        osc_api.enable_throttling()
        for key_id in key_id_not_deleted_list:
            sleep(30)
            self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=key_id)
        if not found_error:
            known_error('GTW-1188', 'Throttling per call for all users does not exist')
        assert False, 'Remove known error'
        assert found_error, "Throttling did not happen"
