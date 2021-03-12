from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_flexible_gpu_state

DEFAULT_GPU_ID = "fgpu-12345678"
DEFAULT_MODEL_NAME = "nvidia-k2"


class Test_UpdateFlexibleGpu(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'gpu_limit': 4}
        cls.fgpu_id = None
        super(Test_UpdateFlexibleGpu, cls).setup_class()
        try:
            ret = cls.a1_r1.oapi.CreateFlexibleGpu(ModelName=DEFAULT_MODEL_NAME,
                                                   SubregionName=cls.a1_r1.config.region.az_name)
            cls.fgpu_id = ret.response.FlexibleGpu.FlexibleGpuId
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.fgpu_id:
                cls.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=cls.fgpu_id)
            wait_flexible_gpu_state(cls.a1_r1, [cls.fgpu_id], cleanup=True)
        finally:
            super(Test_UpdateFlexibleGpu, cls).teardown_class()

    def test_T4641_with_valid_params(self):
        ret = self.a1_r1.oapi.UpdateFlexibleGpu(FlexibleGpuId=self.fgpu_id, DeleteOnVmDeletion=True)
        ret.check_response()
        assert ret.response.FlexibleGpu.DeleteOnVmDeletion
        assert ret.response.FlexibleGpu.FlexibleGpuId == self.fgpu_id
        assert ret.response.FlexibleGpu.ModelName == DEFAULT_MODEL_NAME
        assert ret.response.FlexibleGpu.State == 'allocated'
        assert ret.response.FlexibleGpu.SubregionName == self.a1_r1.config.region.az_name

    def test_T4642_without_id(self):
        try:
            self.a1_r1.oapi.UpdateFlexibleGpu(DeleteOnVmDeletion=True)
            assert False, 'the call should not be successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T4643_without_attr(self):
        ret = self.a1_r1.oapi.UpdateFlexibleGpu(FlexibleGpuId=self.fgpu_id)
        ret.check_response()

    def test_T4644_with_invalid_fgpu_id(self):
        try:
            self.a1_r1.oapi.UpdateFlexibleGpu(FlexibleGpuId='toto')
            assert False, 'the call should not be successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T4645_with_unknown_fgpu_id(self):
        try:
            self.a1_r1.oapi.UpdateFlexibleGpu(FlexibleGpuId='fgpu-12345678')
            assert False, 'the call should not be successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5074')

    def test_T4646_with_invalid_fgpu_id_type(self):
        try:
            self.a1_r1.oapi.UpdateFlexibleGpu(FlexibleGpuId=[self.fgpu_id], DeleteOnVmDeletion=True)
            assert False, 'the call should not be successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T4647_with_invalid_DeleteOnVm_type(self):
        try:
            self.a1_r1.oapi.UpdateFlexibleGpu(FlexibleGpuId=self.fgpu_id, DeleteOnVmDeletion=[True])
            assert False, 'the call should not be successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T4648_with_other_account(self):
        try:
            self.a2_r1.oapi.UpdateFlexibleGpu(FlexibleGpuId=self.fgpu_id)
            assert False, 'the call should not be successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5074')
