import datetime
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_test_tools import misc
from qa_test_tools.misc import assert_dry_run
from qa_tina_tools.test_base import OscTinaTest


class Test_UpdateAccessKey(OscTinaTest):

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
        ak = None
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            ret = self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak, State='ACTIVE')
            ret.check_response()
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4840_invalid_accesskeyid_param(self):
        ak = None
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.oapi.UpdateAccessKey(AccessKeyId='tot', State='ACTIVE')
            assert False, 'Call should not be successful'
        except OscApiException as error:
            misc.assert_error(error, 400, '4122', 'InvalidParameterValue')
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4841_invalid_state_param(self):
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak, State='tot')
            assert False, 'Call should not be successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4123)
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4842_without_state_param(self):
        ak = None
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak)
            assert False, 'Call should not be successful'
        except OscApiException as error:
            misc.assert_error(error, 400, '7000', 'MissingParameter')
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4843_without_accesskeyid_param(self):
        ak = None
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.oapi.UpdateAccessKey(State='ACTIVE')
            assert False, 'Call should not be successful'
        except OscApiException as error:
            misc.assert_error(error, 400, '7000', 'MissingParameter')
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T4844_without_params(self):
        ak = None
        try:
            self.a1_r1.oapi.UpdateAccessKey()
            assert False, 'Call should not be successful'
        except OscApiException as error:
            misc.assert_error(error, 400, '7000', 'MissingParameter')

    def test_T4845_with_method_login_password(self):
        ak = None
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.oapi.UpdateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword},
                                            AccessKeyId=ak, State='ACTIVE')
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T5063_with_dry_run(self):
        ak = None
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            ret = self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak, State='ACTIVE', DryRun=True)
            assert_dry_run(ret)
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T5922_invalid_expiration_date(self):
        ak = None
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak, State='ACTIVE', ExpirationDate='foobar')
            assert False, 'Call should not be successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4123)
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T5923_with_expiration_date(self):
        ak = None
        try:
            exp_date = (datetime.datetime.utcnow() + datetime.timedelta(minutes=1000)).strftime("%Y-%m-%dT%H:%M:%S.000+0000")
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            ret = self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak, State='ACTIVE', ExpirationDate=exp_date)
            assert hasattr(ret.response.AccessKey, 'ExpirationDate')
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)

    def test_T5924_remove_expiration_date(self):
        ak = None
        try:
            exp_date = (datetime.datetime.utcnow() + datetime.timedelta(minutes=1000)).strftime("%Y-%m-%dT%H:%M:%S.000+0000")
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            ret = self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak, State='ACTIVE', ExpirationDate=exp_date)
            assert hasattr(ret.response.AccessKey, 'ExpirationDate')
            ret = self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak, State='ACTIVE')
            assert not hasattr(ret.response.AccessKey, 'ExpirationDate')
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)
