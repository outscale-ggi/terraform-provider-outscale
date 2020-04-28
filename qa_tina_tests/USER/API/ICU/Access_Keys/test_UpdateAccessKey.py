from qa_test_tools.test_base import OscTestSuite
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub.osc_api import AuthMethod
from time import sleep
from qa_sdk_pub import osc_api


class Test_UpdateAccessKey(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateAccessKey, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_UpdateAccessKey, cls).teardown_class()

    def test_T3776_check_throttling(self):
        sleep(30)
        ak = None
        found_error = False
        osc_api.disable_throttling()
        try:
            ak = self.a1_r1.icu.CreateAccessKey().response.accessKey.accessKeyId
            self.a1_r1.icu.UpdateAccessKey(AccessKeyId=ak, Status='active', exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
            for _ in range(3):
                try:
                    self.a1_r1.icu.UpdateAccessKey(AccessKeyId=ak, Status='active', exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                except OscApiException as error:
                    if error.status_code == 503:
                        found_error = True
                    else:
                        raise error
            assert found_error, "Throttling did not happen"
        finally:
            osc_api.enable_throttling()
            if ak is not None:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T3980_valid_params(self):
        sleep(30)
        try:
            ak = self.a1_r1.icu.CreateAccessKey().response.accessKey.accessKeyId
            self.a1_r1.icu.UpdateAccessKey(AccessKeyId=ak, Status='active')
        finally:
            if ak:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T3981_with_method_ak_sk(self):
        ak = None
        sleep(30)
        try:
            ak = self.a1_r1.icu.CreateAccessKey().response.accessKey.accessKeyId
            self.a1_r1.icu.UpdateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk}, AccessKeyId=ak, Status='active')
        finally:
            if ak:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T3982_with_method_login_password(self):
        ak = None
        sleep(30)
        try:
            ak = self.a1_r1.icu.CreateAccessKey().response.accessKey.accessKeyId
            self.a1_r1.icu.UpdateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword}, AccessKeyId=ak, Status='active')
        finally:
            if ak:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)
