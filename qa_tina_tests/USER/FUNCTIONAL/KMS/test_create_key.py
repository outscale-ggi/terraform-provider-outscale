from qa_common_tools.test_base import OscTestSuite, known_error
from osc_common.exceptions.osc_exceptions import OscApiException
import pytest
import datetime
import time


@pytest.mark.region_kms
class Test_create_key(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create_key, cls).setup_class()
        cls.key_id = None
        try:
            cls.account_id = cls.a1_r1.config.account.account_id
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.key_id:
                cls.a1_r1.kms.ScheduleKeyDeletion(KeyId=cls.key_id, PendingWindowInDays=7)
        except OscApiException as error:
            if error.message != "not-implemented - KMS service is not activated":
                raise error
        finally:
            super(Test_create_key, cls).teardown_class()

    def verify_content(self, ret, description=None, key_usage='ENCRYPT_DECRYPT', origin='OKMS'):
        assert hasattr(ret, 'KeyMetadata')
        assert ret.KeyMetadata.Origin == origin
        assert len(ret.KeyMetadata.KeyId) == 12 and ret.KeyMetadata.KeyId[:4] == 'cmk-'
        assert ret.KeyMetadata.Description == description
        assert ret.KeyMetadata.DeletionDate is None
        assert ret.KeyMetadata.KeyManager == 'CUSTOMER'
        assert ret.KeyMetadata.ExpirationModel is None
        assert ret.KeyMetadata.ValidTo is None
        assert ret.KeyMetadata.Enabled is True
        assert ret.KeyMetadata.KeyUsage == key_usage
        assert ret.KeyMetadata.KeyState == 'Enabled'
        assert ret.KeyMetadata.CreationDate
        assert ret.KeyMetadata.Arn
        assert len(ret.KeyMetadata.AWSAccountId) == 12

    def test_T4518_create_key_with_valid_params(self):
        ret = self.a1_r1.kms.CreateKey(Description='description', KeyUsage='ENCRYPT_DECRYPT', Origin='EXTERNAL').response
        self.key_id = ret.KeyMetadata.KeyId
        self.verify_content(ret, description='description', origin='EXTERNAL')
