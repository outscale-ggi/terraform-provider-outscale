from qa_test_tools.test_base import OscTestSuite
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tools.tools.tina.create_tools import create_certificate_setup


class Test_CreateCa(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateCa, cls).setup_class()
        cls.tmp_file_paths = None
        cls.cas = []
        cls.ca1files = cls.ca2files = cls.ca3files = None
        cls.ca1files, cls.ca2files, cls.ca3files, _, _, _, _, cls.tmp_file_paths = create_certificate_setup()
        
    @classmethod
    def teardown_class(cls):
        try:
            for ca_id in cls.cas:
                cls.a1_r1.oapi.DeleteCa(CaId=ca_id)
        finally:
            super(Test_CreateCa, cls).teardown_class()

    def test_T5299_without_params(self):
        try:
            self.a1_r1.oapi.CreateCa()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5300_without_CaPem(self):
        try:
            self.a1_r1.oapi.CreateCa(Description='test ca')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5301_required_params(self):
        with open(self.ca1files[1]) as f:
            ret = self.a1_r1.oapi.CreateCa(CaPem=f.read(), Description='test ca')
        ret.check_response()
        self.cas.append(ret.response.Ca.CaId)

    def test_T5302_with_invalid_CaPem(self):
        try:
            self.a1_r1.oapi.CreateCa(CaPem="test", Description='test ca')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4124')

    def test_T5303_dry_run(self):
        with open(self.ca1files[1]) as f:
            ret = self.a1_r1.oapi.CreateCa(CaPem=f.read(), Description='test ca', DryRun=True)
            assert_dry_run(ret)

    def test_T5304_dry_run_false(self):
        with open(self.ca1files[1]) as f:
            ret = self.a1_r1.oapi.CreateCa(CaPem=f.read(), Description='test ca', DryRun=False)
        self.cas.append(ret.response.Ca.CaId)
