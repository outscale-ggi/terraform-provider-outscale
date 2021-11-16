import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest

DEFAULT_GPU_ID = "fgpu-12345678"
DEFAULT_MODEL_NAME = "nvidia-k2"


@pytest.mark.region_gpu
class Test_DeleteFlexibleGpu(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'gpu_limit': 4}
        super(Test_DeleteFlexibleGpu, cls).setup_class()
        try:
            cls.subregionname = cls.a1_r1.config.region.az_name
            cls.modelname = DEFAULT_MODEL_NAME
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    def test_T4190_missing_flexible_gpu_id(self):
        try:
            self.a1_r1.oapi.DeleteFlexibleGpu()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T4191_unknown_flexible_gpu_id(self):
        try:
            self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=DEFAULT_GPU_ID)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5074')

    def test_T4192_incorrect_flexible_gpu_id(self):
        try:
            self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId='XXXXXXXX')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T4193_invalid_flexible_gpu_id(self):
        try:
            self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=[DEFAULT_GPU_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T4194_invalid_dry_run(self):
        try:
            self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=[DEFAULT_GPU_ID], DryRun='XXXXXXXX')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    @pytest.mark.region_gpu
    def test_T4195_valid_params(self):
        fg_id = None
        try:
            if self.a1_r1.config.region.name == 'in-west-2':
                known_error('BLD-3003', 'no gpu on IN2')
            ret = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=self.modelname, SubregionName=self.subregionname)
            fg_id = ret.response.FlexibleGpu.FlexibleGpuId
            ret = self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=fg_id)
            fg_id = None
            ret.check_response()
        finally:
            if fg_id:
                self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=fg_id)

    def test_T4196_dry_run(self):
        ret = self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=DEFAULT_GPU_ID, DryRun=True)
        assert_dry_run(ret)
