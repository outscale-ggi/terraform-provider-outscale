import re

from time import sleep
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_tina_tools.specs.oapi.check_tools import check_oapi_response
from qa_sdk_pub import osc_api
from qa_sdk_pub.osc_api import AuthMethod


class Test_CreateAccessKey(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'accesskey_limit': 10}
        super(Test_CreateAccessKey, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateAccessKey, cls).teardown_class()

    def test_T4813_non_authenticated(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey(authentication=False)
            ak = ret_create.response.AccessKey.AccessKeyId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 401, '1', 'AccessDenied')
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4814_without_param(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            check_oapi_response(ret_create.response, 'CreateAccessKeyResponse')
            ak = ret_create.response.AccessKey.AccessKeyId
            sk = ret_create.response.AccessKey.SecretKey
            assert re.search(r"([A-Z0-9]{20})", ak), "AK format is not correct"
            assert re.search(r"([A-Z0-9]{40})", sk), "SK format is not correct"
            assert ret_create.response.AccessKey.State == 'ACTIVE'
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4815_param_method_authPassword(self):
        ret_create = None
        try:
            ak = misc.id_generator(size=20)
            sk = misc.id_generator(size=40)
            ret_create = self.a1_r1.oapi.CreateAccessKey(auth=AuthMethod.LoginPassword)
            assert False, 'Remove known error code'
            assert ak == ret_create.response.AccessKey.AccessKeyId, "AccesskeyID created does not correspond AccesskeyID passed"
            assert sk == ret_create.response.AccessKey.SecretKey, "SecrretAccesskey created does not correspond SecrretAccesskey passed"
        except Exception as error:
            known_error('GTW-1240', 'SDK implementation ')
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ret_create.response.AccessKey.AccessKeyId)

    def test_T4816_check_throttling(self):
        found_error = False
        key_id_list = []
        osc_api.disable_throttling()
        try:
            key_id_list.append(self.a1_r1.oapi.CreateAccessKey(max_retry=0).response.AccessKey.AccessKeyId)
            for _ in range(3):
                try:
                    key_id_list.append(self.a1_r1.oapi.CreateAccessKey(max_retry=0).response.AccessKey.AccessKeyId)
                except OscApiException as error:
                    if error.status_code == 503:
                        found_error = True
                    else:
                        raise error
            if not found_error:
                known_error('GTW-1188', 'Throttling per call for all users does not exist')
            assert False, 'Remove known error'
            assert found_error, "Throttling did not happen"
        finally:
            osc_api.enable_throttling()
            for key_id in key_id_list:
                if key_id != key_id_list[0]:
                    sleep(30)
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=key_id)
