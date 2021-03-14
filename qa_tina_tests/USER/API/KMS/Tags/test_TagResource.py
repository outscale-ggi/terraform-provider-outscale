import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_tina_tests.USER.API.KMS.kms import Kms


@pytest.mark.region_kms
class Test_TagResource(Kms):

    @classmethod
    def setup_class(cls):
        cls.key_id = None
        super(Test_TagResource, cls).setup_class()
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
        except OscApiException:
            super(Test_TagResource, cls).teardown_class()

    def test_T3791_missing_key_id(self):
        try:
            self.a1_r1.kms.TagResource(Tags=[{'Key': 'key', 'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field KeyId is required')

    def test_T3792_missing_tags(self):
        try:
            self.a1_r1.kms.TagResource(KeyId=self.key_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field Tags is required')

    def test_T3793_inexistent_key_id(self):
        try:
            self.a1_r1.kms.ListResourceTags(KeyId='cmk-11111111')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'No tags found for the resource: cmk-11111111')

    def test_T3794_other_account(self):
        try:
            self.a2_r1.kms.TagResource(KeyId=self.key_id, Tags=[{'TagKey': 'key', 'TagValue': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotFoundException', 'The customer master key does not exist: {}'.format(self.key_id))

    def test_T3795_valid_params(self):
        self.a1_r1.kms.TagResource(KeyId=self.key_id, Tags=[{'TagKey': 'key', 'TagValue': 'value'}])
        ret = self.a1_r1.kms.ListResourceTags(KeyId=self.key_id)
        assert len(ret.response.Tags) == 1

    def test_T3796_incorrect_tags_type(self):
        try:
            self.a1_r1.kms.TagResource(KeyId=self.key_id, Tags={'TagKey': 'key', 'TagValue': 'value'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Invalid type, Tags must be a list')

    def test_T3797_missing_tags_key(self):
        try:
            self.a2_r1.kms.TagResource(KeyId=self.key_id, Tags=[{'TagValue': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field Tags[].TagKey is required')

    def test_T3798_missing_tags_value(self):
        try:
            self.a2_r1.kms.TagResource(KeyId=self.key_id, Tags=[{'TagKey': 'key'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'KMSClientException', 'Field Tags[].TagValue is required')

    def test_T3799_overwrite(self):
        self.a1_r1.kms.TagResource(KeyId=self.key_id, Tags=[{'TagKey': 'key', 'TagValue': 'value'}])
        ret = self.a1_r1.kms.ListResourceTags(KeyId=self.key_id)
        assert len(ret.response.Tags) == 1
        self.a1_r1.kms.TagResource(KeyId=self.key_id, Tags=[{'TagKey': 'key', 'TagValue': 'value1'}])
        ret = self.a1_r1.kms.ListResourceTags(KeyId=self.key_id)
        assert len(ret.response.Tags) == 1
        assert ret.response.Tags[0].TagValue == 'value1'
