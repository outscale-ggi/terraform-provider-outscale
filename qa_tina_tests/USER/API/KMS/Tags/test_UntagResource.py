import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import known_error
from qa_tina_tests.USER.API.KMS.kms import Kms


@pytest.mark.region_kms
class Test_UntagResource(Kms):

    @classmethod
    def setup_class(cls):
        cls.key_id = None
        super(Test_UntagResource, cls).setup_class()
        try:
            cls.key_id = cls.a1_r1.kms.CreateKey(Description='description', KeyUsage='ENCRYPT_DECRYPT', Origin='EXTERNAL').response.KeyMetadata.KeyId
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.key_id:
                try:
                    cls.a1_r1.kms.ScheduleKeyDeletion(KeyId=cls.key_id, PendingWindowInDays=7)
                except:
                    print('Could not schedule key deletion')
        finally:
            super(Test_UntagResource, cls).teardown_class()

    def test_T3800_missing_key_id(self):
        try:
            self.a1_r1.kms.UntagResource(TagKeys=['key'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field KeyId is required')

    def test_T3801_missing_tag_keys(self):
        try:
            self.a1_r1.kms.UntagResource(KeyId=self.key_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field TagKeys is required')

    def test_T3802_inexistent_key_id(self):
        try:
            self.a1_r1.kms.UntagResource(KeyId='cmk-11111111', TagKeys=['key'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: cmk-11111111')

    def test_T3803_inexistent_tag_key(self):
        try:
            self.a1_r1.kms.UntagResource(KeyId=self.key_id, TagKeys=['key'])
            known_error('TINA-5229', 'OKMS: UntagResource')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert_error(error, 400, '', '')

    def test_T3804_other_account(self):
        try:
            self.a2_r1.kms.UntagResource(KeyId=self.key_id, TagKeys=['key'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: {}'.format(self.key_id))

    def test_T3805_valid_params(self):
        self.a1_r1.kms.TagResource(KeyId=self.key_id, Tags=[{'TagKey': 'key', 'TagValue': 'value'}])
        ret = self.a1_r1.kms.ListResourceTags(KeyId=self.key_id)
        assert len(ret.response.Tags) == 1
        self.a1_r1.kms.UntagResource(KeyId=self.key_id, TagKeys=['key'])
        try:
            ret = self.a1_r1.kms.ListResourceTags(KeyId=self.key_id)
            assert False, 'Remove known error code'
        except OscApiException as error:
            if error.error_code == 'NotFoundException':
                known_error('TINA-5228', 'OKMS: ListResourceTags')
            assert False, 'Remove known error code'
