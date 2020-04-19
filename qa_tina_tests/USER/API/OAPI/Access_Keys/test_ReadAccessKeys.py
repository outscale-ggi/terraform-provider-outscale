from time import sleep
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_sdk_pub import osc_api
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.specs.oapi.check_tools import check_oapi_response
from qa_sdk_pub.osc_api import AuthMethod
from qa_test_tools import misc


class Test_ReadAccessKeys(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadAccessKeys, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ReadAccessKeys, cls).teardown_class()

#     def test_T4827_check_throttling(self):
#         found_error = False
#         osc_api.disable_throttling()
#         key_id = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
#         try:
#             self.a1_r1.oapi.ReadAccessKeys(Filters={'AccessKeyIds': [key_id]}, max_retry=0)
#             for _ in range(3):
#                 try:
#                     self.a1_r1.oapi.ReadAccessKeys(Filters={'AccessKeyIds': [key_id]}, max_retry=0)
#                 except OscApiException as error:
#                     if error.status_code == 503:
#                         found_error = True
#                     else:
#                         raise error
#             if not found_error:
#                 known_error('GTW-1188', 'Throttling per call for all users does not exist')
#             assert False, 'Remove known error'
#             assert found_error, "Throttling did not happen"
#         finally:
#             osc_api.enable_throttling()
#             sleep(30)
#             self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=key_id)

    def test_T4828_without_params(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            resp_read = self.a1_r1.oapi.ReadAccessKeys().response
            check_oapi_response(resp_read, 'ReadAccessKeysResponse')
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4829_with_invalid_params(self):
        ak = misc.id_generator(size=20)
        resp_read = self.a1_r1.oapi.ReadAccessKeys(Filters={'AccessKeyIds': ['toto', ak], 'States': ['tot']}).response
        assert len(resp_read.AccessKeys) == 0

    def test_T4830_with_invalid_accesskeyid(self):
        ak = misc.id_generator(size=20)
        resp_read = self.a1_r1.oapi.ReadAccessKeys(Filters={'AccessKeyIds': ['toto', ak]}).response
        assert len(resp_read.AccessKeys) == 0

    def test_T4831_with_invalid_states(self):
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            resp_read = self.a1_r1.oapi.ReadAccessKeys(Filters={'States': ['tot']}).response
            assert len(resp_read.AccessKeys) == 0
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4832_valid_access_key_state(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            resp_read = self.a1_r1.oapi.ReadAccessKeys(Filters={'AccessKeyIds': [ak], 'States': ['ACTIVE']}).response
            check_oapi_response(resp_read, 'ReadAccessKeysResponse')
            assert len(resp_read.AccessKeys) == 1
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4833_valid_access_key(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            resp_read = self.a1_r1.oapi.ReadAccessKeys(Filters={'AccessKeyIds': [ak]}).response
            check_oapi_response(resp_read, 'ReadAccessKeysResponse')
            assert len(resp_read.AccessKeys) == 1
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4834_valid_state(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            resp_read = self.a1_r1.oapi.ReadAccessKeys(Filters={'States': ['ACTIVE']}).response
            check_oapi_response(resp_read, 'ReadAccessKeysResponse')
            assert len(resp_read.AccessKeys) > 0
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4835_with_method_login_password(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            self.a1_r1.oapi.ReadAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: AuthMethod.LoginPassword}, AccessKeyId=ak)
            assert False, 'remove known error'
        except Exception as error:
            known_error('GTW-1240', 'SDK implementation ')
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4905_without_params_empty_string(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            resp_read = self.a1_r1.oapi.ReadAccessKeys(exec_data={osc_api.EXEC_DATA_FORCE_EMPTY_STRING: True}).response
            check_oapi_response(resp_read, 'ReadAccessKeysResponse')
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)
