import re
from time import sleep

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest


class Test_CreateAccessKey(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'accesskey_limit': 10}
        super(Test_CreateAccessKey, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateAccessKey, cls).teardown_class()

    def test_T3966_non_authenticated(self):
        sleep(30)
        ak = None
        ret_create = None
        try:
            tag = [{'Key': 'Name', 'Value': 'Marketplace'}]
            ret_create = self.a1_r1.icu.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty}, Tag=tag)
            ak = ret_create.response.accessKey.accessKeyId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, 'IcuClientException', 'Field AuthenticationMethod is required')
        finally:
            if ret_create and ak:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T344_without_param(self):
        sleep(30)
        ak = None
        ret_create = None
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            sk = ret_create.response.accessKey.secretAccessKey
            assert ret_create.response.accessKey.ownerId
            assert re.search(r"([A-Z0-9]{20})", ak), "AK format is not correct"
            assert re.search(r"([A-Z0-9]{40})", sk), "SK format is not correct"
            assert ret_create.response.accessKey.status == 'ACTIVE'
            if self.a1_r1.config.account.account_id:
                assert ret_create.response.accessKey.ownerId == self.a1_r1.config.account.account_id
        finally:
            if ret_create and ak:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T3971_param_method_authPassword(self):
        sleep(30)
        ak = None
        ret_create = None
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword})
            ak = ret_create.response.accessKey.accessKeyId
            sk = ret_create.response.accessKey.secretAccessKey
            assert re.search(r"([A-Z0-9]{20})", ak), "AK format is not correct"
            assert re.search(r"([A-Z0-9]{40})", sk), "SK format is not correct"
            assert ret_create.response.accessKey.status == 'ACTIVE'
            if self.a1_r1.config.account.account_id:
                assert ret_create.response.accessKey.ownerId == self.a1_r1.config.account.account_id
        finally:
            if ret_create and ak:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T5987_param_method_authPassword_incorrect(self):
        sleep(30)
        ak = None
        ret_create = None
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                                                   osc_api.EXEC_DATA_LOGIN: 'foo', osc_api.EXEC_DATA_PASSWORD: 'bar'})
            ak = ret_create.response.accessKey.accessKeyId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 403, 'InvalidLoginPassword', 'Account foo failed to authenticate.')
        finally:
            if ret_create and ak:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T3772_check_throttling(self):
        sleep(30)
        found_error = False
        key_id_list = []
        osc_api.disable_throttling()
        try:
            key_id_list.append(self.a1_r1.icu.CreateAccessKey(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0}).response.accessKey.accessKeyId)
            for _ in range(3):
                try:
                    key_id_list.append(self.a1_r1.icu.CreateAccessKey(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0}).response.accessKey.accessKeyId)
                except OscApiException as error:
                    if error.status_code == 503:
                        found_error = True
                    else:
                        raise error
            assert found_error, "Throttling did not happen"
        finally:
            osc_api.enable_throttling()
            for key_id in key_id_list:
                if key_id != key_id_list[0]:
                    sleep(30)
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=key_id)

    def test_T5743_with_extra_param(self):
        sleep(30)
        ak = None
        ret_create = None
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey(Foo='Bar')
            ak = ret_create.response.accessKey.accessKeyId
            sk = ret_create.response.accessKey.secretAccessKey
            assert re.search(r"([A-Z0-9]{20})", ak), "AK format is not correct"
            assert re.search(r"([A-Z0-9]{40})", sk), "SK format is not correct"
            assert ret_create.response.accessKey.status == 'ACTIVE'
            if self.a1_r1.config.account.account_id:
                assert ret_create.response.accessKey.ownerId == self.a1_r1.config.account.account_id
        finally:
            if ret_create and ak:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)
