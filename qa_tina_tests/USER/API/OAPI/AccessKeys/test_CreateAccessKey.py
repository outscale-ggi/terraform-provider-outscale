import re
from time import sleep
import datetime

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from specs import check_tools
from qa_test_tools import misc
from qa_test_tools.misc import assert_dry_run
from qa_tina_tools.test_base import OscTinaTest
from qa_test_tools.test_base import known_error


class Test_CreateAccessKey(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'accesskey_limit': 10}
        super(Test_CreateAccessKey, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateAccessKey, cls).teardown_class()

    def test_T4813_non_authenticated(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty})
            ak = ret_create.response.AccessKey.AccessKeyId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 401, 'AccessDenied', 1)
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4814_without_param(self):
        ret_create = None
        ak = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            sk = ret_create.response.AccessKey.SecretKey
            ret_create.check_response()
            assert hasattr(ret_create.response.AccessKey, "CreationDate")
            assert hasattr(ret_create.response.AccessKey, "LastModificationDate")
            assert not hasattr(ret_create.response.AccessKey, "ExpirationDate")
            assert re.search(r"([A-Z0-9]{20})", ak), "AK format is not correct"
            assert re.search(r"([A-Z0-9]{40})", sk), "SK format is not correct"
            assert ret_create.response.AccessKey.State == 'ACTIVE'
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4815_param_method_authPassword(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword})
            ret_create.check_response()
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ret_create.response.AccessKey.AccessKeyId)

    def test_T5993_param_method_authPassword_incorrect(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                                                    osc_api.EXEC_DATA_LOGIN: 'foo', osc_api.EXEC_DATA_PASSWORD: 'bar'})
            ak = ret_create.response.AccessKey.AccessKeyId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4120)
            known_error('API-400', 'Incorrect error message')
            misc.assert_oapi_error(error, 401, 'AccessDenied', 1)
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T5804_with_expiration_date(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey(
                ExpirationDate=(datetime.datetime.utcnow() + datetime.timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            ak = ret_create.response.AccessKey.AccessKeyId
            sk = ret_create.response.AccessKey.SecretKey
            ret_create.check_response()
            assert hasattr(ret_create.response.AccessKey, "CreationDate")
            assert hasattr(ret_create.response.AccessKey, "LastModificationDate")
            assert hasattr(ret_create.response.AccessKey, "ExpirationDate")
            assert re.search(r"([A-Z0-9]{20})", ak), "AK format is not correct"
            assert re.search(r"([A-Z0-9]{40})", sk), "SK format is not correct"
            assert ret_create.response.AccessKey.State == 'ACTIVE'
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ret_create.response.AccessKey.AccessKeyId)

    def test_T5805_with_incorrect_expiration_date(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey( ExpirationDate='foobar')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_tools.check_oapi_error(error, 4047)
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ret_create.response.AccessKey.AccessKeyId)

    @pytest.mark.skip('obsolete for now, per account per call not supported : gateway-1188')
    def test_T4816_check_throttling(self):
        found_error = False
        key_id_list = []
        osc_api.disable_throttling()
        try:
            key_id_list.append(self.a1_r1.oapi.CreateAccessKey(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0}).response.AccessKey.AccessKeyId)
            for _ in range(3):
                try:
                    key_id_list.append(self.a1_r1.oapi.CreateAccessKey(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0}).response.AccessKey.AccessKeyId)
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
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=key_id)

    def test_T5060_with_DryRun(self):
        ret_create = self.a1_r1.oapi.CreateAccessKey(DryRun=True)
        assert_dry_run(ret_create)
