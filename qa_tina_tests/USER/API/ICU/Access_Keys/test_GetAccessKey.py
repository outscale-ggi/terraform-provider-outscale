from time import sleep

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_test_tools import misc
from qa_tina_tools.test_base import OscTinaTest


class Test_GetAccessKey(OscTinaTest):

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
            self.a1_r1.icu.GetAccessKey(AccessKeyId=key_id, exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
            for _ in range(3):
                try:
                    self.a1_r1.icu.GetAccessKey(AccessKeyId=key_id, exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
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
        ak = None
        ret_create = None
        sleep(30)
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            self.a1_r1.icu.GetAccessKey(AccessKeyId=ak)
        finally:
            if ret_create and ak:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T3976_with_method_ak_sk(self):
        ak = None
        ret_create = None
        sleep(30)
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            self.a1_r1.icu.GetAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk}, AccessKeyId=ak)
        finally:
            if ret_create and ak:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T3977_with_method_login_password(self):
        ak = None
        ret_create = None
        sleep(30)
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            self.a1_r1.icu.GetAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword}, AccessKeyId=ak)
        finally:
            if ret_create and ak:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T5989_with_method_login_password_incorrect(self):
        ak = None
        ret_create = None
        sleep(30)
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            self.a1_r1.icu.GetAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                                   osc_api.EXEC_DATA_LOGIN: 'foo', osc_api.EXEC_DATA_PASSWORD: 'bar'}, AccessKeyId=ak)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 403, 'InvalidLoginPassword', 'Account foo failed to authenticate.')
        finally:
            if ret_create and ak:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T5745_with_extra_param(self):
        ak = None
        ret_create = None
        sleep(30)
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            self.a1_r1.icu.GetAccessKey(AccessKeyId=ak, Foo='Bar')
        finally:
            if ret_create and ak:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)
