from time import sleep

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from specs import check_oapi_error


class Test_DeleteAccessKey(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'accesskey_limit': 10}
        super(Test_DeleteAccessKey, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteAccessKey, cls).teardown_class()

    def test_T4817_without_param(self):
        try:
            self.a1_r1.oapi.DeleteAccessKey()
            assert False, "Call should not have been successful"
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T4818_with_param_but_empty(self):
        try:
            self.a1_r1.oapi.DeleteAccessKey(AccessKeyId='')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T4819_empty_param_with_more_than_one_existing(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            self.a1_r1.oapi.DeleteAccessKey(AccessKeyId='')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            check_oapi_error(error, 7000)
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4820_invalid_accesskeyid_foo(self):
        try:
            self.a1_r1.oapi.DeleteAccessKey(AccessKeyId='foo')
            assert False, "Exception should have been raised"
        except OscApiException as error:
            check_oapi_error(error, 5076)

    def test_T4821_invalid_accesskeyid_validAK_not_existant(self):
        try:
            ak = misc.id_generator(size=20)
            self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)
            assert False, "Exception should have been raised"
        except OscApiException as error:
            check_oapi_error(error, 5076)

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
            check_oapi_error(error, 5076)
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
            ret_delete.check_response()
        finally:
            if ret_create and not ret_delete:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4824_with_method_authLoginPassword(self):
        ret_create = None
        ret_delete = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            ret_delete = self.a1_r1.oapi.DeleteAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword},
                                                         AccessKeyId=ak)
            ret_delete.check_response()
        finally:
            if ret_create and not ret_delete:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T5994_with_method_authLoginPassword_incorrect(self):
        ret_create = None
        ret_delete = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            ret_delete = self.a1_r1.oapi.DeleteAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                                                    osc_api.EXEC_DATA_LOGIN: 'foo', osc_api.EXEC_DATA_PASSWORD: 'bar'},
                                                         AccessKeyId=ak)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4120)
            known_error('API-400', 'Incorrect error message')
            check_oapi_error(error, 1)
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
            check_oapi_error(error, 5076)
        finally:
            if ret_create and not ret_delete:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    @pytest.mark.skip('obsolete for now, per account per call not supported : gateway-1188')
    def test_T4826_check_throttling(self):
        found_error = False
        key_id_list = []
        key_id_not_deleted_list = []
        osc_api.disable_throttling()
        for _ in range(4):
            key_id_list.append(self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId)
        for key_id in key_id_list:
            try:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=key_id, exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
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
        assert found_error, "Throttling did not happen"
