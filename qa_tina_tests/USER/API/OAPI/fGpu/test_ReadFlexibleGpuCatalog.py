import pytest

from qa_sdk_common.exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_test_tools.misc import assert_error, assert_dry_run
from qa_tina_tools.test_base import OscTinaTest
from specs import check_oapi_error


@pytest.mark.region_gpu
class Test_ReadFlexibleGpuCatalog(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'gpu_limit': 4}
        super(Test_ReadFlexibleGpuCatalog, cls).setup_class()

    def test_T4405_no_params(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpuCatalog()
        ret.check_response()
        for cat_item in ret.response.FlexibleGpuCatalog:
            assert cat_item.ModelName
            assert cat_item.MaxRam > 0
            assert cat_item.MaxCpu > 0

    def test_T4406_with_invalid_param(self):
        try:
            self.a1_r1.oapi.ReadFlexibleGpuCatalog(titi='toto')
            assert False, "call should not be passed"
        except OscApiException as err:
            check_oapi_error(err, 3001)

    def test_T4407_with_dryrun_true(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpuCatalog(DryRun=True)
        assert_dry_run(ret)

    def test_T4676_without_authentication(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpuCatalog(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty})
        ret.check_response()
        for cat_item in ret.response.FlexibleGpuCatalog:
            assert cat_item.ModelName
            assert cat_item.MaxRam > 0
            assert cat_item.MaxCpu > 0
