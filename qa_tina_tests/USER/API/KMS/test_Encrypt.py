from qa_test_tools.misc import id_generator, assert_error
import base64
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tests.USER.API.KMS.kms import Kms
import pytest


@pytest.mark.region_kms
class Test_Encrypt(Kms):

    @classmethod
    def setup_class(cls):
        super(Test_Encrypt, cls).setup_class()
        cls.key_metadata = None
        try:
            cls.key_metadata = cls.a1_r1.kms.CreateKey().response.KeyMetadata
        except Exception:
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
            super(Test_Encrypt, cls).teardown_class()

    def test_T3588_valid_params(self):
        encoded_text = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
        ret = self.a1_r1.kms.Encrypt(KeyId=self.key_metadata.KeyId, Plaintext=encoded_text)
        assert ret.response.CiphertextBlob
        assert ret.response.KeyId in self.key_metadata.Arn

    def test_T3589_missing_key_id(self):
        try:
            encoded_text = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
            self.a1_r1.kms.Encrypt(Plaintext=encoded_text)
            assert False, 'Call should not have been successful, missing key id'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field KeyId is required')

    def test_T3590_missing_plain_text(self):
        try:
            self.a1_r1.kms.Encrypt(KeyId=self.key_metadata.KeyId)
            assert False, 'Call should not have been successful, missing plain text'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field Plaintext is required')

    def test_T3591_incorrect_key_id(self):
        try:
            encoded_text = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
            self.a1_r1.kms.Encrypt(KeyId='cmk-11111111', Plaintext=encoded_text)
            assert False, 'Call should not have been successful, incorrect key id'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: cmk-11111111')

    def test_T3592_too_short_plain_text(self):
        try:
            encoded_text = base64.b64encode(''.encode('utf-8')).decode('utf-8')
            self.a1_r1.kms.Encrypt(KeyId=self.key_metadata.KeyId, Plaintext=encoded_text)
            assert False, 'Call should not have been successful, plain text too short'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: PlainText')

    def test_T3593_too_long_plain_text(self):
        try:
            encoded_text = base64.b64encode(id_generator(size=3073).encode('utf-8')).decode('utf-8')
            self.a1_r1.kms.Encrypt(KeyId=self.key_metadata.KeyId, Plaintext=encoded_text)
            assert False, 'Call should not have been successful, plain text too long'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValueLength', "Length of parameter 'PlainText' is invalid: 4100. Expected: {(1, 4096)}.")

    def test_T3594_with_encryption_context(self):
        encoded_text = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
        ret = self.a1_r1.kms.Encrypt(KeyId=self.key_metadata.KeyId, Plaintext=encoded_text, EncryptionContext={'name': 'value'})
        assert ret.response.CiphertextBlob
        assert ret.response.KeyId in self.key_metadata.Arn

    def test_T3606_other_account(self):
        try:
            encoded_text = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
            self.a2_r1.kms.Encrypt(KeyId=self.key_metadata.KeyId, Plaintext=encoded_text)
            assert False, 'Call should not have been successful, incorrect key owner'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: {}'.format(self.key_metadata.KeyId))
