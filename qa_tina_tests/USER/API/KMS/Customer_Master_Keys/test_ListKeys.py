import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import known_error
from qa_tina_tests.USER.API.KMS.kms import Kms


@pytest.mark.region_kms
class Test_ListKeys(Kms):

    kms_num = 101

    @classmethod
    def setup_class(cls):
        cls.quotas = {'cmk_limit': 102}
        cls.known_error = False
        cls.key_ids = []
        super(Test_ListKeys, cls).setup_class()
        try:
            for _ in range(cls.kms_num):
                cls.key_ids.append(cls.a1_r1.kms.CreateKey(Description='description', KeyUsage='ENCRYPT_DECRYPT',
                                                           Origin='OKMS').response.KeyMetadata.KeyId)
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            for key_id in cls.key_ids:
                try:
                    cls.a1_r1.kms.ScheduleKeyDeletion(KeyId=key_id, PendingWindowInDays=7)
                except:
                    print('Could not schedule key deletion.')
        finally:
            super(Test_ListKeys, cls).teardown_class()

    def test_T3600_no_params(self):
        self.a1_r1.kms.ListKeys()

    def test_T3601_valid_params(self):
        try:
            ret = self.a1_r1.kms.ListKeys()
            assert len(ret.response.Keys) == 100
            assert ret.response.NextMarker
            assert False, 'Remove known error code'
        except AssertionError:
            known_error('TINA-4902', 'KMS ListKeys')

    def test_T3602_with_response_limitation(self):
        try:
            ret = self.a1_r1.kms.ListKeys(Limit=1000)
            assert len(ret.response.Keys) == 1000
        except OscApiException as error:
            if error.error_code == 'NotImplemented':
                known_error('TINA-4902', 'KMS ListKeys')
            assert False, 'Remove known error code'

    def test_T3603_with_invalid_response_limitation(self):
        try:
            self.a1_r1.kms.ListKeys(Limit=2000)
        except OscApiException as error:
            if error.error_code == 'NotImplemented':
                known_error('TINA-4902', 'KMS ListKeys')
            assert False, 'Remove known error code'

    def test_T3604_with_invalid_marker(self):
        try:
            self.a1_r1.kms.ListKeys(Marker='toto')
        except OscApiException as error:
            if error.error_code == 'NotImplemented':
                known_error('TINA-4902', 'KMS ListKeys')
            assert False, 'Remove known error code'

    def test_T3605_with_valid_marker(self):
        ret1 = self.a1_r1.kms.ListKeys()
        if ret1.response.Truncated:
            ret2 = self.a1_r1.kms.ListKeys(Marker=ret1.response.NextMarker)
            assert ret1.response.NextMarker != ret2.response.NextMarker

    def test_T3718_other_account(self):
        ret = self.a2_r1.kms.ListKeys()
        assert len(ret.response.Keys) == 1
