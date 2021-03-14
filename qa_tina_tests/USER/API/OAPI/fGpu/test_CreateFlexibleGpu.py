import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite

DEFAULT_MODEL_NAME = "nvidia-k2"


class Test_CreateFlexibleGpu(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'gpu_limit': 4}
        super(Test_CreateFlexibleGpu, cls).setup_class()
        try:
            cls.subregionname = cls.a1_r1.config.region.az_name
            cls.modelname = DEFAULT_MODEL_NAME
        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    def test_T4180_missing_model_name(self):
        try:
            self.a1_r1.oapi.CreateFlexibleGpu(SubregionName=self.subregionname)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T4181_missing_subregion_name(self):
        try:
            self.a1_r1.oapi.CreateFlexibleGpu(ModelName=self.modelname)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T4182_incorrect_model_name(self):
        try:
            self.a1_r1.oapi.CreateFlexibleGpu(ModelName='XXXXXXXX', SubregionName=self.subregionname)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T4183_incorrect_subregion_name(self):
        try:
            self.a1_r1.oapi.CreateFlexibleGpu(SubregionName='XXXXXXXX', ModelName=self.modelname)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5009')

    def test_T4184_invalid_model_name(self):
        try:
            self.a1_r1.oapi.CreateFlexibleGpu(ModelName=[self.modelname], SubregionName=self.subregionname)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T4185_invalid_subregion_name(self):
        try:
            self.a1_r1.oapi.CreateFlexibleGpu(ModelName=self.modelname, SubregionName=[self.subregionname])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    @pytest.mark.region_gpu
    def test_T4303_valid_deletion_on_vm_deletion(self):
        resp = None
        try:
            ret = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=self.modelname, SubregionName=self.subregionname, DeleteOnVmDeletion=False)
            ret.check_response()
            assert not ret.response.FlexibleGpu.DeleteOnVmDeletion
            assert ret.response.FlexibleGpu.ModelName == self.modelname
            assert ret.response.FlexibleGpu.SubregionName == self.subregionname
        finally:
            if resp:
                self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=resp.FlexibleGpu.FlexibleGpuId)

    def test_T4186_invalid_deletion_on_vm_deletion(self):
        try:
            self.a1_r1.oapi.CreateFlexibleGpu(ModelName=self.modelname, SubregionName=self.subregionname, DeleteOnVmDeletion='XXXXXXXX')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T4187_invalid_dry_run(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=self.modelname, SubregionName=self.subregionname, DryRun='XXXXXXXX')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')
        finally:
            if ret:
                self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=ret.response.FlexibleGpu.FlexibleGpuId)

    def test_T4236_without_params(self):
        try:
            self.a1_r1.oapi.CreateFlexibleGpu()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    @pytest.mark.region_gpu
    def test_T4188_valid_params(self):
        resp = None
        try:
            ret = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=DEFAULT_MODEL_NAME, SubregionName=self.subregionname)
            ret.check_response()
            assert not ret.response.FlexibleGpu.DeleteOnVmDeletion
            assert ret.response.FlexibleGpu.ModelName == self.modelname
            assert ret.response.FlexibleGpu.SubregionName == self.subregionname
            assert ret.response.FlexibleGpu.State == 'allocated'
            assert not hasattr(ret.response.FlexibleGpu, 'VmId')
        except Exception as error:
            raise error
        finally:
            if resp:
                self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=resp.FlexibleGpu.FlexibleGpuId)

    def test_T4189_dry_run(self):
        ret = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=self.modelname, SubregionName=self.subregionname, DryRun=True)
        assert_dry_run(ret)

    def test_T4743_dry_run_false(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=self.modelname, SubregionName=self.subregionname, DryRun=False)
            assert_dry_run(ret)
        finally:
            if ret:
                self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=ret.response.FlexibleGpu.FlexibleGpuId)

    @pytest.mark.region_gpu
    def test_T4898_with_generation(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=DEFAULT_MODEL_NAME, SubregionName=self.subregionname, Generation='v4')
            ret.check_response()
            assert not ret.response.FlexibleGpu.DeleteOnVmDeletion
            assert ret.response.FlexibleGpu.Generation == 'v4'
            assert ret.response.FlexibleGpu.ModelName == self.modelname
            assert ret.response.FlexibleGpu.SubregionName == self.subregionname
            assert ret.response.FlexibleGpu.State == 'allocated'
            assert not hasattr(ret.response.FlexibleGpu, 'VmId')
        finally:
            if ret:
                self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=ret.response.FlexibleGpu.FlexibleGpuId)

    @pytest.mark.region_gpu
    def test_T4902_with_unsupported_generation(self):
        try:
            self.a1_r1.oapi.CreateFlexibleGpu(ModelName=DEFAULT_MODEL_NAME, SubregionName=self.subregionname, Generation='v5')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')
        try:
            self.a1_r1.oapi.CreateFlexibleGpu(ModelName=DEFAULT_MODEL_NAME, SubregionName=self.subregionname, Generation='4')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')
        try:
            self.a1_r1.oapi.CreateFlexibleGpu(ModelName=DEFAULT_MODEL_NAME, SubregionName=self.subregionname, Generation=['v5'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')
