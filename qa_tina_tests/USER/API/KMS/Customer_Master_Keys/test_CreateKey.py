import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tests.USER.API.KMS.kms import Kms


def verify_content(ret, description=None, key_usage='ENCRYPT_DECRYPT', origin='OKMS'):
    assert hasattr(ret, 'KeyMetadata')
    assert len(ret.KeyMetadata.KeyId) == 12 and ret.KeyMetadata.KeyId[:4] == 'cmk-'
    assert ret.KeyMetadata.Description == description
    assert ret.KeyMetadata.ExpirationModel is None
    assert ret.KeyMetadata.ValidTo is None
    assert len(ret.KeyMetadata.AWSAccountId) == 12
    assert ret.KeyMetadata.DeletionDate is None
    assert ret.KeyMetadata.KeyUsage == key_usage
    assert ret.KeyMetadata.KeyManager == 'CUSTOMER'
    assert ret.KeyMetadata.CreationDate
    assert ret.KeyMetadata.Arn
    if origin == 'EXTERNAL':
        assert ret.KeyMetadata.Origin == origin
        assert ret.KeyMetadata.Enabled is False
        assert ret.KeyMetadata.KeyState == 'PendingImport'
    else:
        assert ret.KeyMetadata.Origin == origin
        assert ret.KeyMetadata.Enabled is True
        assert ret.KeyMetadata.KeyState == 'Enabled'


@pytest.mark.region_kms
class Test_CreateKey(Kms):

    @classmethod
    def setup_class(cls):
        cls.key_id = None
        super(Test_CreateKey, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_CreateKey, cls).teardown_class()

    def setup_method(self, method):
        Kms.setup_method(self, method)
        self.key_id = None

    def teardown_method(self, method):
        try:
            if self.key_id:
                self.a1_r1.kms.ScheduleKeyDeletion(KeyId=self.key_id, PendingWindowInDays=7)
        finally:
            OscTestSuite.teardown_method(self, method)

    # parameters --> 'Description', 'KeyUsage', 'Origin'
    # Description --> length 0-8192
    # KeyUsage --> ENCRYPT_DECRYPT
    # Origin --> OKMS | EXTERNAL

    def test_T3245_no_params(self):
        ret = self.a1_r1.kms.CreateKey().response
        self.key_id = ret.KeyMetadata.KeyId
        verify_content(ret)

    def test_T3246_valid_params(self):
        ret = self.a1_r1.kms.CreateKey(Description='description', KeyUsage='ENCRYPT_DECRYPT', Origin='EXTERNAL').response
        self.key_id = ret.KeyMetadata.KeyId
        verify_content(ret, description='description', origin='EXTERNAL')

    def test_T3247_invalid_desc_length(self):
        description = id_generator(size=8193)
        try:
            ret = self.a1_r1.kms.CreateKey(Description=description).response
            self.key_id = ret.KeyMetadata.KeyId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValueLength', "Length of parameter 'Description' is invalid: 8193. Expected: {(0, 8192)}.")

    def test_T3248_invalid_key_usage(self):
        try:
            ret = self.a1_r1.kms.CreateKey(KeyUsage='toto').response
            self.key_id = ret.KeyMetadata.KeyId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Value of parameter 'KeyUsage' is not valid: toto. Supported values: ENCRYPT_DECRYPT")

    def test_T3249_invalid_origin(self):
        try:
            ret = self.a1_r1.kms.CreateKey(Origin='toto').response
            self.key_id = ret.KeyMetadata.KeyId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Value of parameter 'Origin' is not valid: toto. Supported values: EXTERNAL, OKMS")

    def test_T4596_verify_default_key(self):
        ret = self.a1_r1.kms.ListKeys()
        ret = self.a1_r1.kms.DescribeKey(KeyId=ret.response.Keys[0].KeyId)
        if ret.response.KeyMetadata.KeyManager == "CUSTOMER":
            known_error('TINA-5305', '[OKMS] Incorrect value for the attribute Manager for the default CMK')
        assert False, 'Remove known error code'
        