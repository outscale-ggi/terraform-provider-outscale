from qa_test_tools.test_base import OscTestSuite
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub.osc_api import AuthMethod
from time import sleep
from qa_sdk_pub import osc_api


class Test_GetAccessKey(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_GetAccessKey, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_GetAccessKey, cls).teardown_class()

    def test_T3774_check_throttling(self):
        sleep(30)
        found_error = False
        osc_api.disable_throttling()
        key_id = self.a1_r1.icu.CreateAccessKey().response.accessKey.accessKeyId
        try:
            self.a1_r1.icu.GetAccessKey(AccessKeyId=key_id, max_retry=0)
            for _ in range(3):
                try:
                    self.a1_r1.icu.GetAccessKey(AccessKeyId=key_id, max_retry=0)
                except OscApiException as error:
                    if error.status_code == 503:
                        found_error = True
                    else:
                        raise error
            assert found_error, "Throttling did not happen"
        finally:
            osc_api.enable_throttling()
            sleep(30)
            self.a1_r1.icu.DeleteAccessKey(AccessKeyId=key_id)

    def test_T3975_valid_access_key(self):
        ret_create = None
        sleep(30)
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            self.a1_r1.icu.GetAccessKey(AccessKeyId=ak)
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T3976_with_method_ak_sk(self):
        ret_create = None
        sleep(30)
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            self.a1_r1.icu.GetAccessKey(auth=AuthMethod.AkSk, AccessKeyId=ak)
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T3977_with_method_login_password(self):
        ret_create = None
        sleep(30)
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            self.a1_r1.icu.GetAccessKey(auth=AuthMethod.LoginPassword, AccessKeyId=ak)
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)
