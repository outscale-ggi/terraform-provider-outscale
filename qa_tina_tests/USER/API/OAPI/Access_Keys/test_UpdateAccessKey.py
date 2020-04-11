from qa_test_tools.test_base import OscTestSuite, known_error
from qa_sdk_pub import osc_api
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_sdk_pub.osc_api import AuthMethod


class Test_UpdateAccessKey(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateAccessKey, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_UpdateAccessKey, cls).teardown_class()

    def test_T4838_check_throttling(self):
        ak = None
        found_error = False
        osc_api.disable_throttling()
        try:
            ak = self.a1_r1.oapi.CreateAccessKey().response.AccessKey.AccessKeyId
            self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak, State='ACTIVE', max_retry=0)
            for _ in range(3):
                try:
                    self.a1_r1.oapi.UpdateAccessKey(AccessKeyId=ak, State='ACTIVE', max_retry=0)
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
            self.a1_r1.oapi.UpdateAccessKey(auth=AuthMethod.LoginPassword, AccessKeyId=ak, State='ACTIVE')
            assert False, 'remove known error'
        except Exception as error:
            known_error('GTW-1240', 'SDK implementation ')
        finally:
            if ak:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=ak)
