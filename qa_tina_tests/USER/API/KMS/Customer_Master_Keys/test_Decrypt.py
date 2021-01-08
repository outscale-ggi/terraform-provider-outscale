import base64

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import known_error
from qa_tina_tests.USER.API.KMS.kms import Kms


@pytest.mark.region_kms
class Test_Decrypt(Kms):

    @classmethod
    def setup_class(cls):
        cls.known_error = False
        super(Test_Decrypt, cls).setup_class()
        cls.key_metadata = None
        try:
            cls.key_metadata = cls.a1_r1.kms.CreateKey().response.KeyMetadata
            cls.data1 = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
            cls.encrypt_data1 = cls.a1_r1.kms.Encrypt(KeyId=cls.key_metadata.KeyId, Plaintext=cls.data1).response
            cls.data2 = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
            cls.encrypt_data2 = cls.a1_r1.kms.Encrypt(KeyId=cls.key_metadata.KeyId, Plaintext=cls.data2, EncryptionContext={'name': 'value'}).response
            cls.data3 = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
            cls.encrypt_data3 = cls.a1_r1.kms.Encrypt(KeyId=cls.key_metadata.KeyId, Plaintext=cls.data3).response

        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            if error.status_code == 500 and error.error_code == 'KMSServerException':
                cls.known_error = True
            else:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.key_metadata:
                try:
                    cls.a1_r1.kms.ScheduleKeyDeletion(KeyId=cls.key_metadata.KeyId, PendingWindowInDays=7)
                except:
                    pass
        finally:
            super(Test_Decrypt, cls).teardown_class()

    def test_T3610_valid_params(self):
        ret = self.a1_r1.kms.Decrypt(CiphertextBlob=self.encrypt_data1.CiphertextBlob)
        assert ret.response.Plaintext == self.data1
        assert ret.response.KeyId == self.key_metadata.KeyId

    def test_T3611_missing_blob(self):
        try:
            self.a1_r1.kms.Decrypt()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field CiphertextBlob is required')

    def test_T3612_incorrect_blob(self):
        try:
            self.a1_r1.kms.Decrypt(CiphertextBlob='11111111')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidCiphertextException', 'Cryptographic operation failed in cipher operation')

    def test_T3613_with_encryption_context(self):
        ret = self.a1_r1.kms.Decrypt(CiphertextBlob=self.encrypt_data2.CiphertextBlob, EncryptionContext={'name': 'value'})
        assert ret.response.Plaintext == self.data2
        assert ret.response.KeyId == self.key_metadata.KeyId

    def test_T3614_incorrect_encryption_context(self):
        try:
            self.a1_r1.kms.Decrypt(CiphertextBlob=self.encrypt_data2.CiphertextBlob, EncryptionContext={'foo': 'bar'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidCiphertextException', 'Cryptographic operation failed in cipher operation')

    def test_T3616_other_account(self):
        try:
            self.a2_r1.kms.Decrypt(CiphertextBlob=self.encrypt_data3.CiphertextBlob)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidCiphertextException', 'Cryptographic operation failed in cipher operation')

    def test_T3615_missing_encryption_context(self):
        self.a1_r1.kms.Decrypt(CiphertextBlob=self.encrypt_data3.CiphertextBlob)
