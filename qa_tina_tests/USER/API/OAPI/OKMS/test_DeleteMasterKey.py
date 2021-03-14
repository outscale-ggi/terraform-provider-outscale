import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_dry_run, \
    assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tests.USER.API.OAPI.OKMS.okms import OKMS


@pytest.mark.region_kms
class Test_DeleteMasterKey(OKMS):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteMasterKey, cls).setup_class()
        cls.key_id = None

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)

    def teardown_method(self, method):
        try:
            if self.key_id:
                try:
                    self.a1_r1.oapi.DeleteMasterKey(MasterKeyId=self.key_id, DaysUntilDeletion=7)
                except:
                    print('Could not delete master key')
        finally:
            OscTestSuite.teardown_method(self, method)

    def mysetup(self, do_delete=False):
        key_id = self.a1_r1.oapi.CreateMasterKey().response.MasterKey.MasterKeyId
        if do_delete:
            self.a1_r1.oapi.DeleteMasterKey(MasterKeyId=key_id, DaysUntilDeletion=7)
        return key_id

    # parameters --> 'KeyId', 'DaysUntilDeletion' (7-30)

    def test_T5160_valid_params(self):
        self.key_id = self.mysetup()
        self.a1_r1.oapi.DeleteMasterKey(MasterKeyId=self.key_id, DaysUntilDeletion=7)

    def test_T5161_missing_key_id(self):
        try:
            self.a1_r1.oapi.DeleteMasterKey(DaysUntilDeletion=7)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5162_missing_pending_window(self):
        self.key_id = self.mysetup()
        self.a1_r1.oapi.DeleteMasterKey(MasterKeyId=self.key_id)

    def test_T5163_invalid_key_id(self):
        try:
            self.a1_r1.oapi.DeleteMasterKey(MasterKeyId='toto', DaysUntilDeletion=7)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T5164_too_long_key_id(self):
        key_id = id_generator(size=2049)
        try:
            self.a1_r1.oapi.DeleteMasterKey(MasterKeyId=key_id, DaysUntilDeletion=7)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T5165_too_small_pending_window(self):
        self.key_id = self.mysetup()
        try:
            self.a1_r1.oapi.DeleteMasterKey(MasterKeyId=self.key_id, DaysUntilDeletion=6)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T5166_too_big_pending_window(self):
        self.key_id = self.mysetup()
        try:
            self.a1_r1.oapi.DeleteMasterKey(MasterKeyId=self.key_id, DaysUntilDeletion=31)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T5167_twice_with_window_change(self):
        self.key_id = self.mysetup(do_delete=True)
        try:
            self.a1_r1.oapi.DeleteMasterKey(MasterKeyId=self.key_id, DaysUntilDeletion=15)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'InvalidState', '6010')

    def test_T5168_dry_run(self):
        self.key_id = self.mysetup()
        ret = self.a1_r1.oapi.DeleteMasterKey(MasterKeyId=self.key_id, DaysUntilDeletion=7, DryRun=True)
        assert_dry_run(ret)
