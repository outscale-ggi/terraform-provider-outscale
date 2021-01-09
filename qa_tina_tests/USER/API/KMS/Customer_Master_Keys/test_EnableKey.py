import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_tina_tests.USER.API.KMS.kms import Kms


@pytest.mark.region_kms
class Test_EnableKey(Kms):

    @classmethod
    def setup_class(cls):
        cls.known_error = False
        super(Test_EnableKey, cls).setup_class()
        try:
            cls.key_id = cls.a1_r1.kms.CreateKey(Description='description', KeyUsage='ENCRYPT_DECRYPT', Origin='OKMS').response.KeyMetadata.KeyId
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
            if cls.key_id:
                try:
                    cls.a1_r1.kms.ScheduleKeyDeletion(KeyId=cls.key_id, PendingWindowInDays=7)
                except:
                    pass
        finally:
            super(Test_EnableKey, cls).teardown_class()

    def test_T3617_no_params(self):
        try:
            self.a1_r1.kms.EnableKey()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field KeyId is required')

    def test_T3618_inexistent_key(self):
        try:
            self.a1_r1.kms.EnableKey(KeyId='cmk-titi')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidCustomerMasterKeyID.Malformed', 'Invalid ID received: cmk-titi')

    def test_T3622_other_account(self):
        try:
            self.a2_r1.kms.EnableKey(KeyId=self.key_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: {}'.format(self.key_id))

    def test_T3619_valid_params(self):
        self.a1_r1.kms.EnableKey(KeyId=self.key_id)
        ret = self.a1_r1.kms.DescribeKey(KeyId=self.key_id)
        assert ret.response.KeyMetadata.KeyState == 'Enabled'
