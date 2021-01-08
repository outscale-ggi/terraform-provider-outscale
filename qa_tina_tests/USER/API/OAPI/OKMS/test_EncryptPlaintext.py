import base64

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_dry_run, \
    assert_oapi_error
from qa_tina_tests.USER.API.OAPI.OKMS.okms import OKMS


@pytest.mark.region_kms
class Test_EncryptPlaintext(OKMS):

    @classmethod
    def setup_class(cls):
        super(Test_EncryptPlaintext, cls).setup_class()
        cls.master_key = None
        try:
            cls.master_key = cls.a1_r1.oapi.CreateMasterKey().response.MasterKey
        except Exception:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.master_key:
                try:
                    cls.a1_r1.oapi.DeleteMasterKey(MasterKeyId=cls.master_key.MasterKeyId, PendingWindowInDays=7)
                except:
                    pass
        finally:
            super(Test_EncryptPlaintext, cls).teardown_class()

    def test_T5169_valid_params(self):
        encoded_text = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
        ret = self.a1_r1.oapi.EncryptPlaintext(MasterKeyId=self.master_key.MasterKeyId, Plaintext=encoded_text)
        ret.check_response()
        assert ret.response.Ciphertext

    def test_T5170_missing_key_id(self):
        try:
            encoded_text = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
            self.a1_r1.oapi.EncryptPlaintext(Plaintext=encoded_text)
            assert False, 'Call should not have been successful, missing key id'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5171_missing_plain_text(self):
        try:
            self.a1_r1.oapi.EncryptPlaintext(MasterKeyId=self.master_key.MasterKeyId)
            assert False, 'Call should not have been successful, missing plain text'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5172_incorrect_key_id(self):
        try:
            encoded_text = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
            self.a1_r1.oapi.EncryptPlaintext(MasterKeyId='cmk-11111111', Plaintext=encoded_text)
            assert False, 'Call should not have been successful, incorrect key id'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5078')

    def test_T5173_too_short_plain_text(self):
        try:
            encoded_text = base64.b64encode(''.encode('utf-8')).decode('utf-8')
            self.a1_r1.oapi.EncryptPlaintext(MasterKeyId=self.master_key.MasterKeyId, Plaintext=encoded_text)
            assert False, 'Call should not have been successful, plain text too short'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5174_too_long_plain_text(self):
        try:
            encoded_text = base64.b64encode(id_generator(size=3073).encode('utf-8')).decode('utf-8')
            self.a1_r1.oapi.EncryptPlaintext(MasterKeyId=self.master_key.MasterKeyId, Plaintext=encoded_text)
            assert False, 'Call should not have been successful, plain text too long'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4106')

    def test_T5175_with_encryption_context(self):
        encoded_text = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
        ret = self.a1_r1.oapi.EncryptPlaintext(MasterKeyId=self.master_key.MasterKeyId, Plaintext=encoded_text, EncryptionContext={'name': 'value'})
        assert ret.response.Ciphertext

    def test_T5176_other_account(self):
        try:
            encoded_text = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
            self.a2_r1.oapi.EncryptPlaintext(MasterKeyId=self.master_key.MasterKeyId, Plaintext=encoded_text)
            assert False, 'Call should not have been successful, incorrect key owner'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5078')

    def test_T5177_with_standard_special_characters(self):
        text = "Th!$ !$ @ text w!th $pec!@£ ch@r@cter$!"
        encoded_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        ret = self.a1_r1.oapi.EncryptPlaintext(MasterKeyId=self.master_key.MasterKeyId, Plaintext=encoded_text)
        assert ret.response.Ciphertext

    def test_T5178_with_special_characters(self):
        text = "test123ù"
        encoded_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        ret = self.a1_r1.oapi.EncryptPlaintext(MasterKeyId=self.master_key.MasterKeyId, Plaintext=encoded_text)
        assert ret.response.Ciphertext

    def test_T5179_dry_run(self):
        encoded_text = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
        ret = self.a1_r1.oapi.EncryptPlaintext(MasterKeyId=self.master_key.MasterKeyId, Plaintext=encoded_text, DryRun=True)
        assert_dry_run(ret)
