import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_tina_tests.USER.API.KMS.kms import Kms


@pytest.mark.region_kms
class Test_CancelKeyDeletion(Kms):

    @classmethod
    def setup_class(cls):
        cls.key_id = None
        super(Test_CancelKeyDeletion, cls).setup_class()

    def setup_method(self, method):
        Kms.setup_method(self, method)
        self.key_id = None

    def teardown_method(self, method):
        try:
            if self.key_id:
                try:
                    self.a1_r1.kms.ScheduleKeyDeletion(KeyId=self.key_id, PendingWindowInDays=7)
                except:
                    print('Could not schedule key deletion.')
        finally:
            Kms.teardown_method(self, method)

    # parameters --> 'KeyId'

    def mysetup(self):
        key_id = self.a1_r1.kms.CreateKey().response.KeyMetadata.KeyId
        self.a1_r1.kms.ScheduleKeyDeletion(KeyId=key_id, PendingWindowInDays=7)
        return key_id

    def test_T3235_valid_params(self):
        self.key_id = self.mysetup()
        ret = self.a1_r1.kms.CancelKeyDeletion(KeyId=self.key_id)
        assert ret.response.KeyId == self.key_id

    def test_T3236_no_params(self):
        try:
            self.a1_r1.kms.CancelKeyDeletion()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field KeyId is required')

    def test_T3237_invalid_key_id(self):
        key_id = id_generator(size=2049)
        try:
            self.a1_r1.kms.CancelKeyDeletion(KeyId=key_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidCustomerMasterKeyID.Malformed', None)

    def test_T3238_unexisting_key_id(self):
        key_id = 'toto'
        try:
            self.a1_r1.kms.CancelKeyDeletion(KeyId=key_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidCustomerMasterKeyID.Malformed', 'Invalid ID received: toto. Expected format: cmk-')
