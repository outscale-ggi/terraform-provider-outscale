from qa_test_tools.misc import assert_error, assert_dry_run
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
import pytest
from qa_tina_tests.USER.API.OAPI.OKMS.okms import OKMS


@pytest.mark.region_kms
class Test_GenerateDataKey(OKMS):

    @classmethod
    def setup_class(cls):
        super(Test_GenerateDataKey, cls).setup_class()
        cls.key_id = None
        try:
            cls.key_metadata = cls.a1_r1.oapi.CreateMasterKey().response.KeyMetadata
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
                    cls.a1_r1.oapi.DeleteMasterKey(MasterKeyId=cls.key_id, DaysUntilDeletion=7)
                except:
                    pass
        finally:
            super(Test_GenerateDataKey, cls).teardown_class()

    def test_T5180_valid_params(self):
        ret = self.a1_r1.oapi.GenerateDataKey(MasterKeyId=self.key_id, Size=8).response
        assert ret.Ciphertext
        assert ret.Plaintext

    def test_T5181_incorrect_key_id(self):
        try:
            self.a1_r1.oapi.GenerateDataKey(MasterKeyId='cmk-11111111', Size=8)
            assert False, 'Call should not have been successful, incorrect key id'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: cmk-11111111')

    def test_T5182_invalid_key_id(self):
        try:
            self.a1_r1.oapi.GenerateDataKey(MasterKeyId='foobar', Size=8)
            assert False, 'Call should not have been successful, invalid key id'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: foobar')

    def test_T5183_missing_key_id(self):
        try:
            self.a1_r1.oapi.GenerateDataKey(Size=8)
            assert False, 'Call should not have been successful, no key id'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field KeyId is required')

    def test_T5184_incorrect_size(self):
        try:
            self.a1_r1.oapi.GenerateDataKey(MasterKeyId=self.key_id, Size='foobar')
            assert False, 'Call should not have been successful, invalid key id'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         "Value of parameter 'KeySpec' is not valid: foobar. Supported values: AES_128, AES_256")

    def test_T5185_missing_size(self):
        try:
            self.a1_r1.oapi.GenerateDataKey(MasterKeyId=self.key_id)
            assert False, 'Call should not have been successful, no key id'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field KeyId is required')

    def test_T5186_with_encryption_context(self):
        ret = self.a1_r1.oapi.GenerateDataKey(MasterKeyId=self.key_id, Size=8, EncryptionContext={'name': 'value'}).response
        assert ret.Ciphertext
        assert ret.Plaintext

    def test_T5187_size_too_small(self):
        try:
            self.a1_r1.oapi.GenerateDataKey(MasterKeyId=self.key_id, Size=0)
            assert False, 'Call should not have been successful, nob too small'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         """Value of parameter 'Size' is not valid: 0. Supported values: (1, 1024), please interpret 'None' as no-limit.""")

    def test_T5188_size_too_big(self):
        try:
            self.a1_r1.oapi.GenerateDataKey(MasterKeyId=self.key_id, Size=1025)
            assert False, 'Call should not have been successful, nob too big'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         """Value of parameter 'Size' is not valid: 1025. Supported values: (1, 1024), please interpret 'None' as no-limit.""")

    def test_T5189_dry_run(self):
        ret = self.a1_r1.oapi.GenerateDataKey(MasterKeyId=self.key_id, Size=8, DryRun=True)
        assert_dry_run(ret)
