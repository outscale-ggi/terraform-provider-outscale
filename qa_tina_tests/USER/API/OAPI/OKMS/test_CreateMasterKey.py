import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_dry_run, \
    assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tests.USER.API.OAPI.OKMS.okms import OKMS


def verify_content( ret, description=None):
    assert hasattr(ret, 'MasterKey')
    assert len(ret.MasterKey.MasterKeyId) == 12 and ret.MasterKey.MasterKeyId[:4] == 'cmk-'
    assert not description or ret.MasterKey.Description == description
    assert not hasattr(ret.MasterKey, 'DeletionDate')
    assert ret.MasterKey.CreationDate
    assert ret.MasterKey.State == 'enabled'


@pytest.mark.region_kms
class Test_CreateMasterKey(OKMS):

    @classmethod
    def setup_class(cls):
        cls.key_id = None
        super(Test_CreateMasterKey, cls).setup_class()

    def setup_method(self, method):
        OKMS.setup_method(self, method)
        self.key_id = None

    def teardown_method(self, method):
        try:
            if self.key_id:
                try:
                    self.a1_r1.oapi.DeleteMasterKey(KeyId=self.key_id, DaysUntilDeletion=7)
                except:
                    print('Could not delete master key')
        finally:
            OscTestSuite.teardown_method(self, method)

    # parameters --> 'Description', 'DryRun'
    # Description --> String : length 0-8192
    # DryRun --> Boolean

    def test_T5147_no_params(self):
        resp = self.a1_r1.oapi.CreateMasterKey().response
        self.key_id = resp.MasterKey.MasterKeyId
        verify_content(resp)

    def test_T5148_valid_params(self):
        ret = self.a1_r1.oapi.CreateMasterKey(Description='description')
        self.key_id = ret.response.MasterKey.MasterKeyId
        verify_content(ret.response, description='description')
        ret.check_response()

    def test_T5149_invalid_desc_length(self):
        description = id_generator(size=8193)
        try:
            ret = self.a1_r1.oapi.CreateMasterKey(Description=description).response
            self.key_id = ret.MasterKey.MasterKeyId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4106')

    def test_T5150_dry_run(self):
        ret = self.a1_r1.oapi.CreateMasterKey(DryRun=True)
        assert_dry_run(ret)
