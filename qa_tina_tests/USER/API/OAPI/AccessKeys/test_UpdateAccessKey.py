import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException, OscSdkException
from qa_sdk_pub import osc_api
from qa_test_tools import misc
from qa_test_tools.misc import assert_dry_run
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_UpdateAccessKey(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateAccessKey, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_UpdateAccessKey, cls).teardown_class()

    @pytest.mark.skip('obsolete for now, per account per call not supported : gateway-1188')
    def test_T4838_check_throttling(self):
        ak = None
        found_error = False
        osc_api.disable_throttling()
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak, State='ACTIVE', exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
            for _ in range(3):
                try:
                    self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak, State='ACTIVE', exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                except OscApiException as error:
                    if error.status_code == 503:
                        found_error = True
                    else:
                        raise error
            assert found_error, "Throttling did not happen"
        finally:
            osc_api.enable_throttling()
            if ak is not None:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4839_valid_params(self):
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak, State='ACTIVE')
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4840_invalid_accesskeyid_param(self):
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.oapi.UpdateAccessKey(AccessKeyId='tot', State='ACTIVE')
        except OscApiException as error:
            misc.assert_error(error, 400, '4122', 'InvalidParameterValue')
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4841_invalid_state_param(self):
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak, State='tot')
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4123)
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4842_without_state_param(self):
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak)
        except OscApiException as error:
            misc.assert_error(error, 400, '7000', 'MissingParameter')
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4843_without_accesskeyid_param(self):
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.oapi.UpdateAccessKey(State='ACTIVE')
        except OscApiException as error:
            misc.assert_error(error, 400, '7000', 'MissingParameter')
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4844_without_params(self):
        try:
            self.a1_r1.oapi.UpdateAccessKey()
        except OscApiException as error:
            misc.assert_error(error, 400, '7000', 'MissingParameter')

    def test_T4845_with_method_login_password(self):
        ak = None
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.oapi.UpdateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword}, AccessKeyId=ak, State='ACTIVE')
            assert False, 'remove known error'
        except OscSdkException as error:
            known_error('GTW-1240', 'SDK implementation ')
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T5063_with_dry_run(self):
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            ret = self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak, State='ACTIVE', DryRun = True)
            assert_dry_run(ret)
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)
