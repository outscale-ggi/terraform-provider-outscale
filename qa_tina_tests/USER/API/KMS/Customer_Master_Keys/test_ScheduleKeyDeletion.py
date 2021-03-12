import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tests.USER.API.KMS.kms import Kms


@pytest.mark.region_kms
class Test_ScheduleKeyDeletion(Kms):

    @classmethod
    def setup_class(cls):
        super(Test_ScheduleKeyDeletion, cls).setup_class()
        cls.key_id = None
        try:
            pass
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_ScheduleKeyDeletion, cls).teardown_class()

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)

    def teardown_method(self, method):
        try:
            if self.key_id:
                try:
                    self.a1_r1.kms.ScheduleKeyDeletion(KeyId=self.key_id, PendingWindowInDays=7)
                except:
                    pass
        finally:
            OscTestSuite.teardown_method(self, method)

    def mysetup(self, no_delete=False):
        key_id = self.a1_r1.kms.CreateKey().response.KeyMetadata.KeyId
        if not no_delete:
            self.a1_r1.kms.ScheduleKeyDeletion(KeyId=key_id, PendingWindowInDays=7)
        return key_id

    # parameters --> 'KeyId', 'PendingWindowInDays' (7-30)

    def test_T3250_valid_params(self):
        self.key_id = self.mysetup(no_delete=True)
        self.a1_r1.kms.ScheduleKeyDeletion(KeyId=self.key_id, PendingWindowInDays=7)

    def test_T3251_missing_key_id(self):
        try:
            self.a1_r1.kms.ScheduleKeyDeletion(PendingWindowInDays=7)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field KeyId is required')

    def test_T3252_missing_pending_window(self):
        self.key_id = self.mysetup(no_delete=True)
        self.a1_r1.kms.ScheduleKeyDeletion(KeyId=self.key_id)

    def test_T3253_invalid_key_id(self):
        try:
            self.a1_r1.kms.ScheduleKeyDeletion(KeyId='toto', PendingWindowInDays=7)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidCustomerMasterKeyID.Malformed', 'Invalid ID received: toto. Expected format: cmk-')

    def test_T3254_too_long_key_id(self):
        key_id = id_generator(size=2049)
        try:
            self.a1_r1.kms.ScheduleKeyDeletion(KeyId=key_id, PendingWindowInDays=7)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidCustomerMasterKeyID.Malformed', 'Invalid ID received: {}. Expected format: cmk-'.format(key_id))

    def test_T3255_too_small_pending_window(self):
        self.key_id = self.mysetup(no_delete=True)
        try:
            self.a1_r1.kms.ScheduleKeyDeletion(KeyId=self.key_id, PendingWindowInDays=6)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Pending window must be between 7 and 30 days.')

    def test_T3256_too_big_pending_window(self):
        self.key_id = self.mysetup(no_delete=True)
        try:
            self.a1_r1.kms.ScheduleKeyDeletion(KeyId=self.key_id, PendingWindowInDays=31)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Pending window must be between 7 and 30 days.')

    def test_T3469_twice_with_window_change(self):
        self.key_id = self.mysetup(no_delete=False)
        try:
            self.a1_r1.kms.ScheduleKeyDeletion(KeyId=self.key_id, PendingWindowInDays=15)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400,
                         'KMSInvalidStateException', 'Invalid state to perform this action: {}. State: pending/deletion'.format(self.key_id))
