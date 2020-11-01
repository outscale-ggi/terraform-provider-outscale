from qa_test_tools.misc import assert_oapi_error, assert_dry_run,\
    compare_validate_objects, id_generator
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
import pytest
from qa_tina_tests.USER.API.OAPI.OKMS.okms import OKMS
from qa_tina_tools.specs.check_tools import check_oapi_response


@pytest.mark.region_kms
class Test_UpdateMasterKey(OKMS):

    @classmethod
    def setup_class(cls):
        cls.known_error = False
        cls.key = None
        super(Test_UpdateMasterKey, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        try:
            if cls.key:
                try:
                    cls.a1_r1.oapi.DeleteMasterKey(MasterKeyId=cls.key.MasterKeyId, DaysUntilDeletion=7)
                except:
                    pass
        finally:
            super(Test_UpdateMasterKey, cls).teardown_class()

    def mysetup(self):
        self.key = self.a1_r1.oapi.CreateMasterKey(Description='description').response.MasterKey

    def setup_method(self, method):
        OKMS.setup_method(self, method)
        self.key = None

    def teardown_method(self, method):
        try:
            if self.key:
                try:
                    self.a1_r1.oapi.DeleteMasterKey(MasterKeyId=self.key.MasterKeyId, DaysUntilDeletion=7)
                except:
                    pass
        finally:
            OKMS.teardown_method(self, method)

    def test_T5218_valid_params(self):
        self.mysetup()
        resp = self.a1_r1.oapi.UpdateMasterKey(MasterKeyId=self.key.MasterKeyId, Description='toto').response
        check_oapi_response(resp, 'UpdateMasterKeyResponse')
        compare_validate_objects(self.key, resp.MasterKey, Description='toto')

    def test_T5219_missing_key_id(self):
        try:
            self.a1_r1.oapi.UpdateMasterKey(Description='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5220_incorrect_key_id(self):
        try:
            self.a1_r1.oapi.UpdateMasterKey(MasterKeyId='cmk-12345678', Description='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5078')

    def test_T5221_invalid_key_id(self):
        try:
            self.a1_r1.oapi.UpdateMasterKey(MasterKeyId='titi', Description='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T5222_no_update_params(self):
        self.mysetup()
        resp = self.a1_r1.oapi.UpdateMasterKey(MasterKeyId=self.key.MasterKeyId).response
        compare_validate_objects(resp.MasterKey, self.key)

    def test_T5230_two_updates(self):
        self.mysetup()
        resp = self.a1_r1.oapi.UpdateMasterKey(MasterKeyId=self.key.MasterKeyId, Description='toto', Enabled=False).response
        compare_validate_objects(self.key, resp.MasterKey,Description='toto', State='disabled')

    def test_T5223_incorrect_description_type(self):
        self.mysetup()
        try:
            self.a1_r1.oapi.UpdateMasterKey(MasterKeyId=self.key.MasterKeyId, Description=['toto'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5224_too_long_description(self):
        self.mysetup()
        new_desc = id_generator(size=9000)
        try:
            self.a1_r1.oapi.UpdateMasterKey(MasterKeyId=self.key.MasterKeyId, Description=new_desc)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4106')

    def test_T5225_empty_description(self):
        self.mysetup()
        resp = self.a1_r1.oapi.UpdateMasterKey(MasterKeyId=self.key.MasterKeyId, Description='').response
        compare_validate_objects(self.key, resp.MasterKey, Description='')

    def test_T5226_incorrect_state_type(self):
        self.mysetup()
        try:
            self.a1_r1.oapi.UpdateMasterKey(MasterKeyId=self.key.MasterKeyId, Enabled=['toto'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5227_invalid_state_value(self):
        self.mysetup()
        try:
            self.a1_r1.oapi.UpdateMasterKey(MasterKeyId=self.key.MasterKeyId, Enabled='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5228_other_account(self):
        self.mysetup()
        try:
            self.a2_r1.oapi.UpdateMasterKey(MasterKeyId=self.key.MasterKeyId, Description='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5078')

    def test_T5229_dry_run(self):
        self.mysetup()
        ret = self.a1_r1.oapi.UpdateMasterKey(MasterKeyId=self.key.MasterKeyId, Description='toto', DryRun=True)
        assert_dry_run(ret)
