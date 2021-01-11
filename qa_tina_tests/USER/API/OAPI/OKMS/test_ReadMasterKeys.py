import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tests.USER.API.OAPI.OKMS.okms import OKMS


@pytest.mark.region_kms
class Test_ReadMasterKeys(OKMS):

    key_num = 6
    disabled_num = 2
    deleted_num = 2

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'cmk_limit': 102}
        cls.known_error = False
        cls.key_ids = []
        super(Test_ReadMasterKeys, cls).setup_class()
        try:
            for i in range(cls.key_num):
                cls.key_ids.append(cls.a1_r1.oapi.CreateMasterKey(Description='description{}'.format(i)).response.MasterKey.MasterKeyId)
            for i in range(cls.disabled_num):
                cls.a1_r1.oapi.UpdateMasterKey(MasterKeyId=cls.key_ids[i], Enabled=False)
            for i in range(cls.deleted_num):
                cls.a1_r1.oapi.DeleteMasterKey(MasterKeyId=cls.key_ids[i + cls.disabled_num], DaysUntilDeletion=7)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            for key_id in cls.key_ids:
                try:
                    cls.a1_r1.oapi.DeleteMasterKey(MasterKeyId=key_id, DaysUntilDeletion=7)
                except:
                    pass
        finally:
            super(Test_ReadMasterKeys, cls).teardown_class()

    def test_T5196_no_params(self):
        ret = self.a1_r1.oapi.ReadMasterKeys()
        ret.check_response()
        assert len(ret.response.MasterKeys) == self.key_num + 1

    def test_T5197_with_filter_description(self):
        descriptions = ['description0', 'description2']
        ret = self.a1_r1.oapi.ReadMasterKeys(Filters={'Descriptions': descriptions})
        assert len(ret.response.MasterKeys) == 2
        assert set([key.Description for key in ret.response.MasterKeys]) == set(descriptions)

    def test_T5198_with_filter_keyid(self):
        keyids = [self.key_ids[0], self.key_ids[2]]
        ret = self.a1_r1.oapi.ReadMasterKeys(Filters={'MasterKeyIds': keyids})
        assert len(ret.response.MasterKeys) == 2
        assert set([key.MasterKeyId for key in ret.response.MasterKeys]) == set(keyids)

    def test_T5199_with_filter_states(self):
        states = ['disabled', 'pending/deletion']
        ret = self.a1_r1.oapi.ReadMasterKeys(Filters={'States': states})
        assert len(ret.response.MasterKeys) == self.disabled_num + self.deleted_num
        assert set([key.State for key in ret.response.MasterKeys]) == set(states)

    def test_T5200_with_filter_two_criteria(self):
        states = ['disabled', 'pending/deletion']
        descriptions = ['description0', 'description2']
        ret = self.a1_r1.oapi.ReadMasterKeys(Filters={'States': states, 'Descriptions': descriptions})
        assert len(ret.response.MasterKeys) == 2
        assert set([key.MasterKeyId for key in ret.response.MasterKeys]) == set([self.key_ids[0], self.key_ids[2]])

    def test_T5201_with_invalid_filter(self):
        try:
            self.a1_r1.oapi.ReadMasterKeys(Filters={'foo': 'bar'})
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T5202_with_invalid_filter_type(self):
        try:
            self.a1_r1.oapi.ReadMasterKeys(Filters='foobar')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5203_dry_run(self):
        ret = self.a1_r1.oapi.ReadMasterKeys(DryRun=True)
        assert_dry_run(ret)
        
    def test_T5204_other_account(self):
        ret = self.a2_r1.oapi.ReadMasterKeys()
        assert len(ret.response.MasterKeys) == 1
