from qa_common_tools.misc import assert_error
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tests.USER.API.KMS.kms import Kms
import pytest


@pytest.mark.region_kms
class Test_GenerateDataKey(Kms):

    @classmethod
    def setup_class(cls):
        super(Test_GenerateDataKey, cls).setup_class()
        cls.key_metadata = None
        try:
            cls.key_metadata = cls.a1_r1.kms.CreateKey().response.KeyMetadata
        except:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.key_metadata:
                try:
                    cls.a1_r1.kms.ScheduleKeyDeletion(KeyId=cls.key_metadata.KeyId, PendingWindowInDays=7)
                except:
                    pass
        finally:
            super(Test_GenerateDataKey, cls).teardown_class()

    def test_T3623_valid_params_key_spec(self):
        ret = self.a1_r1.kms.GenerateDataKey(KeyId=self.key_metadata.KeyId, KeySpec='AES_128').response
        assert ret.CiphertextBlob
        assert ret.KeyId
        assert ret.Plaintext

    def test_T3624_valid_params_nob(self):
        ret = self.a1_r1.kms.GenerateDataKey(KeyId=self.key_metadata.KeyId, NumberOfBytes=8).response
        assert ret.CiphertextBlob
        assert ret.KeyId
        assert ret.Plaintext

    def test_T3625_incorrect_key_id(self):
        try:
            self.a1_r1.kms.GenerateDataKey(KeyId='cmk-11111111', KeySpec='AES_128')
            assert False, 'Call should not have been successful, incorrect key id'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: cmk-11111111')

    def test_T3626_invalid_key_id(self):
        try:
            self.a1_r1.kms.GenerateDataKey(KeyId='foobar', KeySpec='AES_128')
            assert False, 'Call should not have been successful, invalid key id'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: foobar')

    def test_T3627_missing_key_id_with_keyspec(self):
        try:
            self.a1_r1.kms.GenerateDataKey(KeySpec='AES_128')
            assert False, 'Call should not have been successful, no key id'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field KeyId is required')

    def test_T3628_missing_key_id_with_nob(self):
        try:
            self.a1_r1.kms.GenerateDataKey(NumberOfBytes=8)
            assert False, 'Call should not have been successful, no key id'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field KeyId is required')

    def test_T3629_incorrect_key_spec(self):
        try:
            self.a1_r1.kms.GenerateDataKey(KeyId=self.key_metadata.KeyId, KeySpec='foobar')
            assert False, 'Call should not have been successful, invalid key id'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         "Value of parameter 'KeySpec' is not valid: foobar. Supported values: AES_128, AES_256")

    def test_T3630_with_encryption_context(self):
        ret = self.a1_r1.kms.GenerateDataKey(KeyId=self.key_metadata.KeyId, KeySpec='AES_128', EncryptionContext={'name': 'value'}).response
        assert ret.CiphertextBlob
        assert ret.KeyId
        assert ret.Plaintext

    def test_T3631_too_small_nob(self):
        try:
            self.a1_r1.kms.GenerateDataKey(KeyId=self.key_metadata.KeyId, NumberOfBytes=0)
            assert False, 'Call should not have been successful, nob too small'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         """Value of parameter 'NumberOfBytes' is not valid: 0. Supported values: (1, 1024), please interpret 'None' as no-limit.""")

    def test_T3632_too_big_nob(self):
        try:
            self.a1_r1.kms.GenerateDataKey(KeyId=self.key_metadata.KeyId, NumberOfBytes=1025)
            assert False, 'Call should not have been successful, nob too big'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         """Value of parameter 'NumberOfBytes' is not valid: 1025. Supported values: (1, 1024), please interpret 'None' as no-limit.""")

    def test_T3633_nob_and_key_spec(self):
        try:
            self.a1_r1.kms.GenerateDataKey(KeyId=self.key_metadata.KeyId, KeySpec='AES_128', NumberOfBytes=8)
            assert False, 'Call should not have been successful, both keyspec and nob specified'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterCombination',
                         'These parameters cannot be provided together: KeySpec, numberOfBytes. Expected at most: 1')
