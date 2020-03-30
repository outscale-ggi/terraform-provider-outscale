from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import assert_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite
import pytest
from qa_tina_tools.specs.oapi.check_tools import check_oapi_response

#     ReadGpuCatalogRequest:
#       properties:
#         DryRun: {description: ReadGpuCatalogRequest_DryRun, type: boolean}
#       type: object
#     ReadGpuCatalogResponse:
#       properties:
#         GpuCatalogs:
#           description: ReadGpuCatalogResponse_GpuCatalogs
#           items: {$ref: '#/components/schemas/GpuCatalog'}
#           type: array
#         ResponseContext: {$ref: '#/components/schemas/ResponseContext'}
#       type: object


@pytest.mark.region_gpu
class Test_ReadFlexibleGpuCatalog(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'gpu_limit': 4}
        super(Test_ReadFlexibleGpuCatalog, cls).setup_class()
        try:
            pass
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_ReadFlexibleGpuCatalog, cls).teardown_class()

    def test_T4405_no_params(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpuCatalog()
        check_oapi_response(ret.response, 'ReadFlexibleGpuCatalogResponse')
        for cat_item in ret.response.FlexibleGpuCatalog:
            assert cat_item.ModelName
            assert cat_item.MaxRam > 0
            assert cat_item.MaxCpu > 0

    def test_T4406_with_invalid_param(self):
        try:
            self.a1_r1.oapi.ReadFlexibleGpuCatalog(titi='toto')
            assert False, "call should not be passed"
        except OscApiException as err:
            assert_error(err, 400, '3001', 'InvalidParameter')

    def test_T4407_with_dryrun_true(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpuCatalog(DryRun=True)
        assert_dry_run(ret)

    def test_T4676_without_authentication(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpuCatalog(authentication=False)
        check_oapi_response(ret.response, 'ReadFlexibleGpuCatalogResponse')
        for cat_item in ret.response.FlexibleGpuCatalog:
            assert cat_item.ModelName
            assert cat_item.MaxRam > 0
            assert cat_item.MaxCpu > 0
