from qa_test_tools.misc import id_generator, assert_error, assert_dry_run
import base64
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
import pytest
from qa_tina_tests.USER.API.OAPI.OKMS.okms import OKMS
from qa_tina_tools.specs.check_tools import check_oapi_response


@pytest.mark.region_kms
class Test_DecryptCipherText(OKMS):

    @classmethod
    def setup_class(cls):
        super(Test_DecryptCipherText, cls).setup_class()
        cls.master_key_id = None
        try:
            cls.master_key_id = cls.a1_r1.oapi.CreateKey().response.MasterKey.MasterKeyId
            cls.data1 = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
            cls.encrypt_data1 = cls.a1_r1.oapi.EncryptPlaintext(MasterKeyId=cls.master_key_id, Plaintext=cls.data1).response
            cls.data2 = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
            cls.encrypt_data2 = cls.a1_r1.oapi.EncryptPlaintext(MasterKeyId=cls.master_key_id, Plaintext=cls.data2, EncryptionContext={'name': 'value'}).response
            cls.data3 = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
            cls.encrypt_data3 = cls.a1_r1.oapi.EncryptPlaintext(MasterKeyId=cls.master_key_id, Plaintext=cls.data3).response

        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.key_metadata:
                try:
                    cls.a1_r1.oapi.DeleteMasterKey(MasterKeyId=cls.master_key_id, DaysUntilDeletion=7)
                except:
                    pass
        finally:
            super(Test_DecryptCipherText, cls).teardown_class()

    # parameters --> 'CipherText', 'DryRun', 'EncryptionContext'
    # CipherText --> String
    # DryRun --> Boolean
    # EncryptionContext --> Map

    def test_T5151_valid_params(self):
        ret = self.a1_r1.oapi.DecryptCipherText(Ciphertext=self.encrypt_data1.Ciphertext)
        assert ret.response.Plaintext == self.data1
        assert ret.response.KeyId == self.master_key_id
        check_oapi_response(ret.response, 'DecryptCiphertextResponse')

    def test_T5152_missing_cipher_text(self):
        try:
            self.a1_r1.oapi.DecryptCipherText()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field CiphertextBlob is required')

    def test_T5153_incorrect_cipher_text(self):
        try:
            self.a1_r1.oapi.DecryptCipherText(Ciphertext='11111111')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidCiphertextException', 'Cryptographic operation failed in cipher operation')

    def test_T5154_with_encryption_context(self):
        ret = self.a1_r1.oapi.DecryptCipherText(Ciphertext=self.encrypt_data2.Ciphertext, EncryptionContext={'name': 'value'})
        assert ret.response.Plaintext == self.data2
        assert ret.response.MasterKeyId == self.master_key_id

    def test_T5155_incorrect_encryption_context(self):
        try:
            self.a1_r1.oapi.DecryptCipherText(Ciphertext=self.encrypt_data2.Ciphertext, EncryptionContext={'foo': 'bar'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidCiphertextException', 'Cryptographic operation failed in cipher operation')

    def test_T5156_missing_needed_encryption_context(self):
        try:
            self.a1_r1.oapi.DecryptCipherText(Ciphertext=self.encrypt_data2.Ciphertext)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidCiphertextException', 'Cryptographic operation failed in cipher operation')

    def test_T5157_other_account(self):
        try:
            self.a2_r1.oapi.DecryptCipherText(Ciphertext=self.encrypt_data3.Ciphertext)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidCiphertextException', 'Cryptographic operation failed in cipher operation')

    def test_T5158_missing_encryption_context(self):
        self.a1_r1.oapi.DecryptCipherText(Ciphertext=self.encrypt_data3.Ciphertext)

    def test_T5159_dry_run(self):
        ret = self.a1_r1.oapi.DecryptCipherText(Ciphertext=self.encrypt_data2.Ciphertext, EncryptionContext={'name': 'value'}, DryRun=True)
        assert_dry_run(ret)
