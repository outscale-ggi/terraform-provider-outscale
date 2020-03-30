from qa_test_tools.test_base import OscTestSuite
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tools.specs.oapi.check_tools import check_oapi_response
import pytest

#     CreateFlexibleGpuRequest:
#       properties:
#         DeleteOnVmDeletion: {default: false, description: CreateFlexibleGpuRequest_DeleteOnVmDeletion,
#           type: boolean}
#         DryRun: {description: CreateFlexibleGpuRequest_DryRun, type: boolean}
#         ModelName: {description: CreateFlexibleGpuRequest_ModelName, type: string}
#         SubregionName: {description: CreateFlexibleGpuRequest_SubregionName, type: string}
#       required: [ModelName, SubregionName]
#       type: object
#     CreateFlexibleGpuResponse:
#       properties:
#         FlexibleGpu: {$ref: '#/components/schemas/FlexibleGpu'}
#         ResponseContext: {$ref: '#/components/schemas/ResponseContext'}
#       type: object

DEFAULT_MODEL_NAME = "nvidia-k2"


class Test_CreateFlexibleGpu(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'gpu_limit': 4}
        super(Test_CreateFlexibleGpu, cls).setup_class()
        try:
            cls.subregionname = cls.a1_r1.config.region.az_name
            cls.modelname = DEFAULT_MODEL_NAME
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
            super(Test_CreateFlexibleGpu, cls).teardown_class()

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
            resp = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=self.modelname, SubregionName=self.subregionname, DeleteOnVmDeletion=False).response
            check_oapi_response(resp, 'CreateFlexibleGpuResponse')
            assert not resp.FlexibleGpu.DeleteOnVmDeletion
            assert resp.FlexibleGpu.ModelName == self.modelname
            assert resp.FlexibleGpu.SubregionName == self.subregionname
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
        try:
            self.a1_r1.oapi.CreateFlexibleGpu(ModelName=self.modelname, SubregionName=self.subregionname, DryRun='XXXXXXXX')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

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
            resp = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=DEFAULT_MODEL_NAME, SubregionName=self.subregionname).response
            check_oapi_response(resp, 'CreateFlexibleGpuResponse')
            assert not resp.FlexibleGpu.DeleteOnVmDeletion
            assert resp.FlexibleGpu.ModelName == self.modelname
            assert resp.FlexibleGpu.SubregionName == self.subregionname
            assert resp.FlexibleGpu.State == 'allocated'
            assert not hasattr(resp.FlexibleGpu, 'VmId')
        finally:
            if resp:
                self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=resp.FlexibleGpu.FlexibleGpuId)

    def test_T4189_dry_run(self):
        ret = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=self.modelname, SubregionName=self.subregionname, DryRun=True)
        assert_dry_run(ret)

    def test_T4743_dry_run_false(self):
        ret = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=self.modelname, SubregionName=self.subregionname, DryRun=False)
        assert_dry_run(ret)

    @pytest.mark.region_gpu
    def test_T4898_with_generation(self):
        resp = None
        try:
            resp = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=DEFAULT_MODEL_NAME, SubregionName=self.subregionname, Generation='v4').response
            check_oapi_response(resp, 'CreateFlexibleGpuResponse')
            assert not resp.FlexibleGpu.DeleteOnVmDeletion
            assert resp.FlexibleGpu.Generation == 'v4'
            assert resp.FlexibleGpu.ModelName == self.modelname
            assert resp.FlexibleGpu.SubregionName == self.subregionname
            assert resp.FlexibleGpu.State == 'allocated'
            assert not hasattr(resp.FlexibleGpu, 'VmId')
        finally:
            if resp:
                self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=resp.FlexibleGpu.FlexibleGpuId)
