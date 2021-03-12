import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_certificate_setup


class Test_UpdateCa(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateCa, cls).setup_class()
        cls.tmp_file_paths = None
        cls.ca_id = None
        cls.ca1files = cls.ca2files = cls.ca3files = None
        cls.ca1files, cls.ca2files, cls.ca3files, _, _, _, _, cls.tmp_file_paths = create_certificate_setup()
        with open(cls.ca1files[1]) as cafile:
            cls.ca_id = cls.a1_r1.oapi.CreateCa(CaPem=cafile.read(), Description='test ca').response.Ca.CaId

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ca_id:
                cls.a1_r1.oapi.DeleteCa(CaId=cls.ca_id)
        finally:
            super(Test_UpdateCa, cls).teardown_class()

    def test_T5317_without_params(self):
        try:
            self.a1_r1.oapi.UpdateCa()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5318_required_params(self):
        ret = self.a1_r1.oapi.UpdateCa(CaId=self.ca_id, Description='test update')
        ret.check_response()
        assert ret.response.Ca.Description == 'test update'

    def test_T5319_With_DryRun(self):
        ret = self.a1_r1.oapi.UpdateCa(CaId=self.ca_id, Description='test update', DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T5320_with_other_account(self):
        try:
            self.a2_r1.oapi.UpdateCa(CaId=self.ca_id, Description='test update')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4122')
