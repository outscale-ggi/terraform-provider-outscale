from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_dry_run,\
    assert_oapi_error
import pytest
from qa_tina_tests.USER.API.OAPI.OKMS.okms import OKMS
from qa_tina_tools.specs.check_tools import check_oapi_response
from qa_test_tools.test_base import known_error


@pytest.mark.region_kms
class Test_UndeleteMasterKey(OKMS):

    @classmethod
    def setup_class(cls):
        super(Test_UndeleteMasterKey, cls).setup_class()
        try:
            pass
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_UndeleteMasterKey, cls).teardown_class()

    def setup_method(self, method):
        OKMS.setup_method(self, method)
        self.key_id = None

    def teardown_method(self, method):
        try:
            if self.key_id:
                try:
                    self.a1_r1.oapi.DeleteMasterKey(MasterKeyId=self.key_id, DaysUntilDeletion=7)
                except:
                    pass
        finally:
            OKMS.teardown_method(self, method)

    # parameters --> 'MasterKeyId', 'DryRun'
    # MasterKeyId --> String
    # DryRun --> Boolean

    def mysetup(self):
        key_id = self.a1_r1.oapi.CreateMasterKey().response.MasterKey.MasterKeyId
        self.a1_r1.oapi.DeleteMasterKey(MasterKeyId=key_id, DaysUntilDeletion=7)
        return key_id

    def test_T5212_valid_params(self):
        try:
            self.key_id = self.mysetup()
            ret = self.a1_r1.oapi.UndeleteMasterKey(MasterKeyId=self.key_id)
            assert False, "Remove known error code"
            assert ret.response.MasterKey.MasterKeyId == self.key_id
            check_oapi_response(ret.response, 'UndeleteMasterKeyResponse')
        except OscApiException as error:
            if error.message == "InternalError":
                known_error("TINA-6046", "kms.key.cancel_deletion return Internal error")
            assert_oapi_error(error, 400, '', '')

    def test_T5213_no_params(self):
        try:
            self.a1_r1.oapi.UndeleteMasterKey()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5214_invalid_key_id(self):
        key_id = id_generator(size=2049)
        try:
            self.a1_r1.oapi.UndeleteMasterKey(MasterKeyId=key_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T5215_unexisting_key_id(self):
        key_id = 'toto'
        try:
            self.a1_r1.oapi.UndeleteMasterKey(MasterKeyId=key_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T5216_dry_run(self):
        ret = self.a1_r1.oapi.CreateMasterKey(DryRun=True)
        assert_dry_run(ret)

    def test_T5217_from_another_account(self):
        self.key_id = self.mysetup()
        try:
            self.a2_r1.oapi.UndeleteMasterKey(MasterKeyId=self.key_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            self.key_id = None
            assert_oapi_error(error, 400, 'InvalidResource', '5078')
