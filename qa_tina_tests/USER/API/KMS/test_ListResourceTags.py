from qa_test_tools.misc import assert_error
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tests.USER.API.KMS.kms import Kms
import pytest


@pytest.mark.region_kms
class Test_ListResourceTags(Kms):

    @classmethod
    def setup_class(cls):
        super(Test_ListResourceTags, cls).setup_class()
        try:
            cls.key_id = cls.a1_r1.kms.CreateKey(Description='description', KeyUsage='ENCRYPT_DECRYPT', Origin='EXTERNAL').response.KeyMetadata.KeyId
            cls.a1_r1.kms.TagResource(KeyId=cls.key_id, Tags=[{'TagKey': 'key', 'TagValue': 'value'}])
        except:
            try:
                cls.teardown_class()
            except Exception:
                pass

    @classmethod
    def teardown_class(cls):
        try:
            if cls.key_id:
                try:
                    cls.a1_r1.kms.ScheduleKeyDeletion(KeyId=cls.key_id, PendingWindowInDays=7)
                except:
                    pass
        finally:
            super(Test_ListResourceTags, cls).teardown_class()

    def test_T3787_no_params(self):
        try:
            self.a1_r1.kms.ListResourceTags()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field KeyId is required')

    def test_T3788_inexistent_key(self):
        try:
            self.a1_r1.kms.ListResourceTags(KeyId='cmk-11111111')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'No tags found for the resource: cmk-11111111')

    def test_T3790_other_account(self):
        try:
            self.a2_r1.kms.ListResourceTags(KeyId=self.key_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'No tags found for the resource: {}'.format(self.key_id))

    def test_T3789_valid_params(self):
        ret = self.a1_r1.kms.ListResourceTags(KeyId=self.key_id)
        assert len(ret.response.Tags) == 1
