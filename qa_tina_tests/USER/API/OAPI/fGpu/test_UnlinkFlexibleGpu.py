from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_flexible_gpu_state
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
import pytest

#     UnlinkFlexibleGpuRequest:
#       properties:
#         DryRun: {description: UnlinkFlexibleGpuRequest_DryRun, type: boolean}
#         FlexibleGpuId: {description: UnlinkFlexibleGpuRequest_FlexibleGpuId, type: string}
#       required: [FlexibleGpuId]
#       type: object
#     UnlinkFlexibleGpuResponse:
#       properties:
#         ResponseContext: {$ref: '#/components/schemas/ResponseContext'}
#       type: object

DEFAULT_MODEL_NAME = "nvidia-k2"


@pytest.mark.region_gpu
class Test_UnlinkFlexibleGpu(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'gpu_limit': 4}
        cls.inst_info = None
        cls.fg_id = None
        cls.ret_link = None
        super(Test_UnlinkFlexibleGpu, cls).setup_class()
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
        finally:
            super(Test_UnlinkFlexibleGpu, cls).teardown_class()

    def setup_method(self, method):
        self.ret_link = None
        OscTestSuite.setup_method(self, method)
        try:
            self.ret_link = self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=self.fg_id, VmId=self.inst_info[INSTANCE_ID_LIST][0])
            wait_flexible_gpu_state(self.a1_r1, [self.fg_id], state='attaching')
        except OscApiException as error:
            raise error

    def teardown_method(self, method):
        try:
            if self.ret_link:
                self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=self.fg_id)
                self.ret_link = None
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T4208_missing_flexible_gpu_id(self):
        try:
            self.a1_r1.oapi.UnlinkFlexibleGpu()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T4209_invalid_flexible_gpu_id(self):
        try:
            self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=['fgpu-12345678'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T4210_incorrect_flexible_gpu_id(self):
        try:
            self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId='XXXXXXXXXX')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T4211_unknown_flexible_gpu_id(self):
        try:
            self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId='fgpu-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5074')

    def test_T4212_invalid_dry_run(self):
        try:
            self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=self.fg_id, DryRun='XXXXXXXX')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T4213_valid_params(self):
        ret_unlink = self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=self.fg_id).response
        self.ret_link = None
        wait_flexible_gpu_state(self.a1_r1, [self.fg_id], state='allocated')
        ret_unlink.check_response()

    def test_T4214_dry_run(self):
        ret = self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=self.fg_id, DryRun=True)
        assert_dry_run(ret)
