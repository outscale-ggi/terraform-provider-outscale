from time import sleep

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException, OscSdkException
from qa_sdk_pub import osc_api
from qa_test_tools import misc
from qa_test_tools.misc import assert_dry_run
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_ReadAccessKeys(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadAccessKeys, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ReadAccessKeys, cls).teardown_class()

    @pytest.mark.skip('obsolete for now, per account per call not supported : gateway-1188')
    def test_T4827_check_throttling(self):
        found_error = False
        osc_api.disable_throttling()
        key_id = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
        try:
            self.a1_r1.oapi.ReadAccessKeys(Filters={'AccessKeyIds': [key_id]}, max_retry=0)
            for _ in range(3):
                try:
                    self.a1_r1.oapi.ReadAccessKeys(Filters={'AccessKeyIds': [key_id]}, max_retry=0)
                except OscApiException as error:
                    if error.status_code == 503:
                        found_error = True
                    else:
                        raise error
            assert found_error, "Throttling did not happen"
        finally:
            osc_api.enable_throttling()
            sleep(30)
            self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=key_id)

    def test_T4828_without_params(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            ret = self.a1_r1.oapi.ReadAccessKeys()
            ret.check_response()
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
            ret = self.a1_r1.oapi.ReadAccessKeys(Filters={'AccessKeyIds': [ak], 'States': ['ACTIVE']})
            ret.check_response()
            assert len(ret.response.AccessKeys) == 1
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4833_valid_access_key(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            ret = self.a1_r1.oapi.ReadAccessKeys(Filters={'AccessKeyIds': [ak]})
            ret.check_response()
            assert len(ret.response.AccessKeys) == 1
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4834_valid_state(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            ret = self.a1_r1.oapi.ReadAccessKeys(Filters={'States': ['ACTIVE']})
            ret.check_response()
            assert len(ret.response.AccessKeys) > 0
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4835_with_method_login_password(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            self.a1_r1.oapi.ReadAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword}, AccessKeyId=ak)
            assert False, 'remove known error'
        except OscSdkException:
            known_error('GTW-1240', 'SDK implementation ')
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4905_without_params_empty_string(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.oapi.CreateAccessKey()
            ak = ret_create.response.AccessKey.AccessKeyId
            ret = self.a1_r1.oapi.ReadAccessKeys(exec_data={osc_api.EXEC_DATA_FORCE_EMPTY_STRING: True})
            ret.check_response()
        finally:
            if ret_create:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T5061_with_DryRun(self):
        ret_create = self.a1_r1.oapi.ReadAccessKeys(DryRun=True)
        assert_dry_run(ret_create)
