from qa_test_tools.misc import assert_error, assert_dry_run
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
import pytest
from qa_tina_tests.USER.API.OAPI.OKMS.okms import OKMS
from qa_tina_tools.specs.check_tools import check_oapi_response


@pytest.mark.region_kms
class Test_UpdateMasterKey(OKMS):

    @classmethod
    def setup_class(cls):
        cls.known_error = False
        super(Test_UpdateMasterKey, cls).setup_class()
        try:
            cls.key_id = cls.a1_r1.oapi.CreateMasterKey(Description='description').response.MasterKey.KeyId
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
                try:
                    cls.a1_r1.oapi.DeleteMasterKey(MasterKeyId=cls.key_id, DaysUntilDeletion=7)
                except:
                    pass
        finally:
            super(Test_UpdateMasterKey, cls).teardown_class()

    def test_T5218_valid_params(self):
        master_key = self.a1_r1.oapi.ReadMasterKeys().response.MasterKeys[0]
        resp = self.a1_r1.oapi.UpdateMasterKey(MasterKeyId=self.key_id, Description='toto').response
        check_oapi_response(resp, 'UpdateMasterKeyResponse')
        assert resp.MasterKey.CreationDate == master_key.CreationDate
        assert resp.MasterKey.DeleteionDate == master_key.DeleteionDate
        assert resp.MasterKey.Description == 'toto'
        assert resp.MasterKey.MasterKeyId == master_key.MasterKeyId
        assert resp.MasterKey.State == master_key.State

    def test_T5219_missing_key_id(self):
        try:
            self.a1_r1.oapi.UpdateMasterKey(Description='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, '', '')

    def test_T5220_incorrect_key_id(self):
        try:
            self.a1_r1.oapi.UpdateMasterKey(MasterKeyId='cmk-12345678', Description='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, '', '')

    def test_T5221_invalid_key_id(self):
        try:
            self.a1_r1.oapi.UpdateMasterKey(MasterKeyId='titi', Description='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, '', '')

    def test_T5222_no_update_params(self):
        master_key = self.a1_r1.oapi.ReadMasterKeys().response.MasterKeys[0]
        resp = self.a1_r1.oapi.UpdateMasterKey(MasterKeyId=self.key_id).response
        assert resp.MasterKey.CreationDate == master_key.CreationDate
        assert resp.MasterKey.DeleteionDate == master_key.DeleteionDate
        assert resp.MasterKey.Description == master_key.Description
        assert resp.MasterKey.MasterKeyId == master_key.MasterKeyId
        assert resp.MasterKey.State == master_key.State

    def test_T5230_two_updates(self):
        pass

    def test_T5223_incorrect_description_type(self):
        pass

    def test_T5224_too_long_description(self):
        pass

    def test_T5225_empty_description(self):
        pass

    def test_T5226_incorrect_state_type(self):
        pass

    def test_T5227_invalid_state_value(self):
        pass

    def test_T5228_other_account(self):
        try:
            self.a2_r1.oapi.UpdateMasterKey(MasterKeyId=self.key_id, Description='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, '', '')

    def test_T5229_dry_run(self):
        ret = self.a1_r1.oapi.UpdateMasterKey(MasterKeyId=self.key_id, Description='toto', DryRun=True)
        assert_dry_run(ret)
