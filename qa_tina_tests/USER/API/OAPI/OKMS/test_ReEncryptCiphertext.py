from qa_test_tools.misc import id_generator, assert_error, assert_dry_run
import base64
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
import pytest
from qa_tina_tests.USER.API.OAPI.OKMS.okms import OKMS
from qa_tina_tools.specs.check_tools import check_oapi_response


@pytest.mark.region_kms
class Test_ReEncryptCiphertext(OKMS):
    pass
#     @classmethod
#     def setup_class(cls):
#         cls.master_key_id = None
#         super(Test_ReEncryptCiphertext, cls).setup_class()
#         try:
#             cls.master_key_id = cls.a1_r1.oapi.CreateMasterKey().response.MasterKey.MasterKeyId
#         except Exception:
#             try:
#                 cls.teardown_class()
#             except Exception:
#                 pass
#             raise
# 
#     @classmethod
#     def teardown_class(cls):
#         try:
#             if cls.master_key_id:
#                 try:
#                     cls.a1_r1.oapi.DeleteMasterKey(KeyId=cls.master_key_id, DaysUntilDeletion=7)
#                 except:
#                     pass
#         finally:
#             super(Test_ReEncryptCiphertext, cls).teardown_class()
# 
#     def setup_method(self, method):
#         OKMS.setup_method(self, method)
#         self.orig_master_key_id = None
#         try:
#             self.orig_master_key_id = self.a1_r1.oapi.CreateMasterKey().response.MasterKey.MasterKeyId
#             self.orig_encryption_context = {'name': 'value'}
#             encoded_text = base64.b64encode(id_generator(size=128).encode('utf-8')).decode('utf-8')
#             self.cipher_text = self.a1_r1.oapi.EncryptPlaintext(MasterKeyId=self.orig_master_key_id, Plaintext=encoded_text, EncryptionContext=self.orig_encryption_context).response.Ciphertext
#         except:
#             try:
#                 self.teardown_method(method)
#             except:
#                 pass
#             raise
# 
#     def teardown_method(self, method):
#         try:
#             if self.orig_master_key_id:
#                 self.a1_r1.oapi.DeleteMasterKey(MasterKeyId=self.orig_master_key_id, DaysUntilDeletion=7)
#         finally:
#             OKMS.teardown_method(self, method)       
# 
#     def test_T5205_valid_params(self):
#         resp = self.a1_r1.oapi.ReEncryptCiphertext(NewMasterKeyId=self.master_key_id, OriginalCiphertext=self.cipher_text, OriginalEncryptionContext=self.orig_encryption_context).response
#         check_oapi_response(resp, 'ReEncryptCiphertextResponse')
#         assert resp.Ciphertext
#         assert resp.OriginalMasterKeyId == self.master_key_id
# 
#     def test_T5206_missing_new_key_id(self):
#         try:
#             self.a1_r1.oapi.ReEncryptCiphertext(OriginalCiphertext=self.cipher_text, OriginalEncryptionContext=self.orig_encryption_context).response
#             assert False, 'Call should not have been successful, missing key id'
#         except OscApiException as error:
#             assert_error(error, 400, '', '')
# 
#     def test_T5207_missing_orig_cipher_text(self):
#         try:
#             self.a1_r1.oapi.ReEncryptCiphertext(NewMasterKeyId=self.master_key_id, OriginalEncryptionContext=self.orig_encryption_context).response
#             assert False, 'Call should not have been successful, missing cipher text'
#         except OscApiException as error:
#             assert_error(error, 400, '', '')
# 
#     def test_T5208_missing_orig_encryption_context(self):
#         try:
#             self.a1_r1.oapi.ReEncryptCiphertext(NewMasterKeyId=self.master_key_id, OriginalCiphertext=self.cipher_text).response
#             assert False, 'Call should not have been successful, missing key id'
#         except OscApiException as error:
#             assert_error(error, 400, '', '')
# 
#     def test_T5209_incorrect_orig_cipher_text(self):
#         try:
#             self.a1_r1.oapi.ReEncryptCiphertext(NewMasterKeyId=self.master_key_id, OriginalCiphertext='toto', OriginalEncryptionContext=self.orig_encryption_context).response
#             assert False, 'Call should not have been successful, missing key id'
#         except OscApiException as error:
#             assert_error(error, 400, '', '')
# 
#     def test_T5210_incorrect_orig_encryption_context(self):
#         try:
#             self.a1_r1.oapi.ReEncryptCiphertext(NewMasterKeyId=self.master_key_id, OriginalCiphertext='toto', OriginalEncryptionContext={'foo': 'bar'}).response
#             assert False, 'Call should not have been successful, missing key id'
#         except OscApiException as error:
#             assert_error(error, 400, '', '')
# 
#     def test_T5211_dry_run(self):
#         ret = self.a1_r1.oapi.ReEncryptCiphertext(NewMasterKeyId=self.master_key_id, OriginalCiphertext=self.cipher_text, OriginalEncryptionContext=self.orig_encryption_context, DryRun=True)
#         assert_dry_run(ret)
