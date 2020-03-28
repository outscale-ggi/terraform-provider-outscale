from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
import pytest
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.wait_tools import wait_flexible_gpu_state
from qa_common_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.specs.oapi.check_tools import check_oapi_response
from osc_common.exceptions.osc_exceptions import OscApiException

#     LinkFlexibleGpuRequest:
#       properties:
#         DryRun: {description: LinkFlexibleGpuRequest_DryRun, type: boolean}
#         FlexibleGpuId: {description: LinkFlexibleGpuRequest_FlexibleGpuId, type: string}
#         VmId: {description: LinkFlexibleGpuRequest_VmId, type: string}
#       required: [FlexibleGpuId, VmId]
#       type: object
#     LinkFlexibleGpuResponse:
#       properties:
#         ResponseContext: {$ref: '#/components/schemas/ResponseContext'}
#       type: object

DEFAULT_MODEL_NAME = "nvidia-k2"


@pytest.mark.region_gpu
class Test_LinkFlexibleGpu(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'gpu_limit': 4}
        cls.inst_info = None
        cls.fg_id = None
        super(Test_LinkFlexibleGpu, cls).setup_class()
        try:
            cls.inst_info = create_instances(cls.a1_r1, inst_type='tinav4.c10r10')
            cls.fg_id = cls.a1_r1.oapi.CreateFlexibleGpu(ModelName=DEFAULT_MODEL_NAME,
                                                         SubregionName=cls.a1_r1.config.region.az_name).response.FlexibleGpu.FlexibleGpuId
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.fg_id:
                cls.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=cls.fg_id)
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_LinkFlexibleGpu, cls).teardown_class()

    def test_T4197_missing_vm_id(self):
        try:
            self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=self.fg_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T4198_incorrect_vm_id(self):
        try:
            self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=self.fg_id, VmId='XXXXXXXX')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T4199_invalid_vm_id(self):
        try:
            self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=self.fg_id, VmId=['i-12345678'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T4200_unknown_vm_id(self):
        try:
            self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=self.fg_id, VmId='i-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')

    def test_T4201_missing_flexible_gpu_id(self):
        try:
            self.a1_r1.oapi.LinkFlexibleGpu(VmId=self.inst_info[INSTANCE_ID_LIST][0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T4202_incorrect_flexible_gpu_id(self):
        try:
            self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId='XXXXXXXX', VmId=self.inst_info[INSTANCE_ID_LIST][0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T4203_unknown_flexible_gpu_id(self):
        try:
            self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId='fgpu-12345678', VmId=self.inst_info[INSTANCE_ID_LIST][0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5074')

    def test_T4204_invalid_flexible_gpu_id(self):
        try:
            self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=['fgpu-12345678'], VmId=self.inst_info[INSTANCE_ID_LIST][0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T4205_invalid_dry_run(self):
        try:
            self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=self.fg_id, VmId=self.inst_info[INSTANCE_ID_LIST][0], DryRun='XXXXXXXX')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T4206_valid_params(self):
        ret_link = None
        try:
            ret_link = self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=self.fg_id, VmId=self.inst_info[INSTANCE_ID_LIST][0])
            wait_flexible_gpu_state(self.a1_r1, [self.fg_id], state='attaching')
            check_oapi_response(ret_link.response, 'LinkFlexibleGpuResponse')
        finally:
            if ret_link:
                self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=self.fg_id)

    def test_T4207_dry_run(self):
        ret = self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=self.fg_id, VmId=self.inst_info[INSTANCE_ID_LIST][0], DryRun=True)
        assert_dry_run(ret)
