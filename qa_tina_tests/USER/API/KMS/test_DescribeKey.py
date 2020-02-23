from qa_common_tools.misc import assert_error
from osc_common.exceptions.osc_exceptions import OscApiException, OscTestException
from qa_tina_tests.USER.API.KMS.kms import Kms
import pytest


@pytest.mark.region_kms
class Test_DescribeKey(Kms):

    @classmethod
    def setup_class(cls):
        cls.known_error = False
        super(Test_DescribeKey, cls).setup_class()
        try:
            cls.key_id = cls.a1_r1.kms.CreateKey(Description='description', KeyUsage='ENCRYPT_DECRYPT', Origin='EXTERNAL').response.KeyMetadata.KeyId
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
            super(Test_DescribeKey, cls).teardown_class()

    def test_T3595_no_params(self):
        try:
            self.a1_r1.kms.DescribeKey()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field KeyId is required')

    def test_T3596_valid_params(self):
        ret = self.a1_r1.kms.DescribeKey(KeyId=self.key_id)
        assert ret.response.KeyMetadata.KeyId == self.key_id
        assert ret.response.KeyMetadata.AWSAccountId == self.a1_r1.config.account.account_id

    def test_T3597_invalid_prefix_key(self):
        try:
            self.a1_r1.kms.DescribeKey(KeyId='titi')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: titi')

    def test_T3598_inexistent_key(self):
        try:
            self.a1_r1.kms.DescribeKey(KeyId='cmk-11111111')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: cmk-11111111')

    def test_T3599_invalid_params(self):
        try:
            self.a1_r1.kms.DescribeKey(KeyId='titi', toto='titi')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: titi')

    def test_T3621_other_account(self):
        try:
            self.a2_r1.kms.DescribeKey(KeyId=self.key_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: {}'.format(self.key_id))
