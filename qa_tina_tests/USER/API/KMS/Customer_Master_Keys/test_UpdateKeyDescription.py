from qa_test_tools.misc import assert_error, id_generator
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tests.USER.API.KMS.kms import Kms
import pytest


@pytest.mark.region_kms
class Test_UpdateKeyDescription(Kms):

    @classmethod
    def setup_class(cls):
        cls.key_id = None
        super(Test_UpdateKeyDescription, cls).setup_class()
        try:
            cls.key_id = cls.a1_r1.kms.CreateKey(Description='description', KeyUsage='ENCRYPT_DECRYPT', Origin='EXTERNAL').response.KeyMetadata.KeyId
        except Exception:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.key_id:
                try:
                    cls.a1_r1.kms.ScheduleKeyDeletion(KeyId=cls.key_id, PendingWindowInDays=7)
                except:
                    pass
        finally:
            super(Test_UpdateKeyDescription, cls).teardown_class()

    def test_T3634_no_params(self):
        try:
            self.a1_r1.kms.UpdateKeyDescription()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field KeyId is required')

    def test_T3635_valid_params(self):
        self.a1_r1.kms.UpdateKeyDescription(KeyId=self.key_id, Description='test')
        ret = self.a1_r1.kms.DescribeKey(KeyId=self.key_id)
        assert ret.response.KeyMetadata.Description == 'test'

    def test_T3636_inexistent_key(self):
        try:
            self.a1_r1.kms.UpdateKeyDescription(KeyId='cmk-11111111', Description='test')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: cmk-11111111')

    def test_T3637_invalid_params(self):
        try:
            self.a1_r1.kms.UpdateKeyDescription(KeyId='titi', toto='titi', Description='test')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: titi')

    def test_T3638_other_account(self):
        try:
            self.a2_r1.kms.UpdateKeyDescription(KeyId=self.key_id, Description='test')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: {}'.format(self.key_id))

    def test_T3650_missing_key(self):
        try:
            self.a1_r1.kms.UpdateKeyDescription(Description='test')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field KeyId is required')

    def test_T3651_missing_description(self):
        try:
            self.a1_r1.kms.UpdateKeyDescription(KeyId=self.key_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field Description is required')

    def test_T3652_invalid_description_value(self):
        description = id_generator(size=10000)
        try:
            self.a1_r1.kms.UpdateKeyDescription(KeyId=self.key_id, Description=description)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValueLength', "Length of parameter 'Description' is invalid: 10000. Expected: {(0, 8192)}.")
