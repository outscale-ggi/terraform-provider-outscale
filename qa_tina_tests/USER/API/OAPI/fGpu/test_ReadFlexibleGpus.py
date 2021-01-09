import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_flexible_gpu_state


#     ReadFlexibleGpusRequest:
#       properties:
#         DryRun: {description: ReadGpuRequest_DryRun, type: boolean}
#         Filters: {$ref: '#/components/schemas/FiltersFlexibleGpu'}
#       type: object
#     ReadFlexibleGpusResponse:
#       properties:
#         FlexibleGpus:
#           description: ReadGpuResponse_FlexibleGpus
#           items: {$ref: '#/components/schemas/FlexibleGpu'}
#           type: array
#         ResponseContext: {$ref: '#/components/schemas/ResponseContext'}
#       type: object
#     FiltersFlexibleGpu:
#       description: FiltersFlexibleGpu
#       properties:
#         DeleteOnVmDeletion: {description: FiltersFlexibleGpu_DeleteOnVmDeletion, type: boolean}
#         ModelNames:
#           description: FiltersFlexibleGpu_ModelNames
#           items: {type: string}
#           type: array
#         States:
#           description: FiltersFlexibleGpu_States
#           items: {type: string}
#           type: array
#         SubregionNames:
#           description: FiltersFlexibleGpu_SubregionNames
#           items: {type: string}
#           type: array
#         VmIds:
#           description: FiltersFlexibleGpu_VmIds
#           items: {type: string}
#           type: array
#       type: object
@pytest.mark.region_gpu
class Test_ReadFlexibleGpus(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'gpu_limit': 4}
        super(Test_ReadFlexibleGpus, cls).setup_class()
        try:
            cls.max_fgpu = 4
            cls.gpus_id_1 = None
            cls.gpus_id_2 = None
            cls.gpus_id_3 = None
            cls.res_link_1 = None
            cls.res_link_2 = None
            cls.insufficient_capacity = False
            cls.single_account = False
            cls.inst_info_1 = None
            cls.inst_info_2 = None
            cls.region_name_1 = cls.a1_r1.config.region.az_name
            ret = cls.a1_r1.intel.pci.find_gpu_reservations()
            if cls.max_fgpu - len(ret.response.result) < 2:
                cls.insufficient_capacity = True
                return
            if cls.max_fgpu - len(ret.response.result) < 3:
                cls.single_account = True
            cls.inst_info_1 = create_instances(cls.a1_r1, nb=2, inst_type=cls.a1_r1.config.region.get_info(constants.DEFAULT_GPU_INSTANCE_TYPE))
            if not cls.single_account:
                cls.inst_info_2 = create_instances(cls.a2_r1, nb=2, inst_type=cls.a2_r1.config.region.get_info(constants.DEFAULT_GPU_INSTANCE_TYPE))
            cls.gpus_id_1 = cls.a1_r1.oapi.CreateFlexibleGpu(ModelName='nvidia-k2',
                                                             SubregionName=cls.region_name_1).response.FlexibleGpu.FlexibleGpuId
            cls.gpus_id_2 = cls.a1_r1.oapi.CreateFlexibleGpu(ModelName='nvidia-k2',
                                                             SubregionName=cls.region_name_1).response.FlexibleGpu.FlexibleGpuId
            cls.res_link_1 = cls.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=cls.gpus_id_1, VmId=cls.inst_info_1[INSTANCE_ID_LIST][0])
            if not cls.single_account:
                cls.gpus_id_3 = cls.a2_r1.oapi.CreateFlexibleGpu(ModelName='nvidia-k2',
                                                                 SubregionName=cls.region_name_1).response.FlexibleGpu.FlexibleGpuId
                cls.res_link_2 = cls.a2_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=cls.gpus_id_3, VmId=cls.inst_info_2[INSTANCE_ID_LIST][0])
            wait_flexible_gpu_state(cls.a1_r1, [cls.gpus_id_1], state="attaching")
            if not cls.single_account:
                wait_flexible_gpu_state(cls.a2_r1, [cls.gpus_id_3], state="attaching")
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.res_link_1:
                cls.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=cls.gpus_id_1)
                # wait_flexible_gpu_state(cls.a1_r1, [cls.gpus_id_1], state="allocated")
            if cls.gpus_id_1:
                cls.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=cls.gpus_id_1)
            if cls.gpus_id_2:
                cls.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=cls.gpus_id_2)
            if cls.inst_info_1:
                delete_instances(cls.a1_r1, cls.inst_info_1)
            if not cls.single_account:
                if cls.res_link_2:
                    cls.a2_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=cls.gpus_id_3)
                    # wait_flexible_gpu_state(cls.a2_r1, [cls.gpus_id_3], state="allocated")
                if cls.gpus_id_3:
                    cls.a2_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=cls.gpus_id_3)
                if cls.inst_info_2:
                    delete_instances(cls.a2_r1, cls.inst_info_2)
        finally:
            super(Test_ReadFlexibleGpus, cls).teardown_class()

    def test_T4223_filters_model_name(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'ModelNames': ['nvidia-k2']}).response.FlexibleGpus
        assert len(res) == 2
        res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'ModelNames': ['nvidia-m60']}).response.FlexibleGpus
        assert len(res) == 0
        if not self.single_account:
            res = self.a2_r1.oapi.ReadFlexibleGpus(Filters={'ModelNames': ['nvidia-k2']}).response.FlexibleGpus
            assert len(res) == 1
            res = self.a2_r1.oapi.ReadFlexibleGpus(Filters={'ModelNames': ['nvidia-m60']}).response.FlexibleGpus
            assert len(res) == 0

    def test_T4224_filters_model_name_value_non_existent(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'ModelNames': ['toto']}).response.FlexibleGpus
        assert len(res) == 0

    def test_T4225_filters_state_attached(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'States': ['attached']}).response.FlexibleGpus
        assert len(res) == 0
        if not self.single_account:
            res = self.a2_r1.oapi.ReadFlexibleGpus(Filters={'States': ['attached']}).response.FlexibleGpus
            assert len(res) == 0

    def test_T4226_filters_correct_subregions(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'SubregionNames': [self.region_name_1]}).response.FlexibleGpus
        assert len(res) == 2
        if not self.single_account:
            res = self.a2_r1.oapi.ReadFlexibleGpus(Filters={'SubregionNames': [self.region_name_1]}).response.FlexibleGpus
            assert len(res) == 1

    def test_T4227_filters_state_allocated(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        try:
            self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=self.gpus_id_1)
            wait_flexible_gpu_state(self.a1_r1, [self.gpus_id_1], state="allocated")
            res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'States': ['allocated']}).response.FlexibleGpus
            assert len(res) == 2
            if not self.single_account:
                res = self.a2_r1.oapi.ReadFlexibleGpus(Filters={'States': ['allocated']}).response.FlexibleGpus
                assert len(res) == 0
        except OscApiException as error:
            raise error
        finally:
            self.res_link_1 = self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=self.gpus_id_1, VmId=self.inst_info_1[INSTANCE_ID_LIST][0])
            wait_flexible_gpu_state(self.a1_r1, [self.gpus_id_1], state="attaching")

    def test_T4228_filters_modelname_and_state(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        try:
            res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'States': ['attaching'], 'ModelNames': ['nvidia-k2']}).response.FlexibleGpus
            assert len(res) == 1
            res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'States': ['attaching'], 'ModelNames': ['nvidia-m60']}).response.FlexibleGpus
            assert len(res) == 0
            self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=self.gpus_id_1)
            wait_flexible_gpu_state(self.a1_r1, [self.gpus_id_1], state="allocated")
            self.res_link_1 = None
            res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'States': ['allocated'], 'ModelNames': ['nvidia-k2']}).response.FlexibleGpus
            res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'States': ['allocated'], 'ModelNames': ['nvidia-m60']}).response.FlexibleGpus
        except OscApiException as error:
            raise error
        finally:
            if not self.res_link_1:
                self.res_link_1 = self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=self.gpus_id_1, VmId=self.inst_info_1[INSTANCE_ID_LIST][0])
                wait_flexible_gpu_state(self.a1_r1, [self.gpus_id_1], state="attaching")

    def test_T4229_filters_modelname_state_and_subregions(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        try:
            res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'States': ['attached'], 'ModelNames': ['nvidia-k2'],
                                                            'SubregionNames': [self.region_name_1]}).response.FlexibleGpus
            assert len(res) == 0
            res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'States': ['attached'], 'ModelNames': ['nvidia-m60'],
                                                            'SubregionNames': [self.region_name_1]}).response.FlexibleGpus
            assert len(res) == 0
#             res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'State': 'Attached', 'ModelName': 'nvidia-m60',
#                                                             'SubregionNames': self.region_name_2}).response.FlexibleGpus
#             assert len(res) == 0
#             res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'State': 'Attached', 'ModelName': 'nvidia-k2',
#                                                             'SubregionNames': self.region_name_2}).response.FlexibleGpus
#             assert len(res) == 0
            self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=self.gpus_id_1)
            wait_flexible_gpu_state(self.a1_r1, [self.gpus_id_1], state="allocated")
            self.res_link_1 = None
            res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'States': ['allocated'], 'ModelNames': ['nvidia-k2'],
                                                            'SubregionNames': [self.region_name_1]}).response.FlexibleGpus
            assert len(res) == 2
            res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'States': ['allocated'], 'ModelNames': ['nvidia-m60'],
                                                            'SubregionNames': [self.region_name_1]}).response.FlexibleGpus
            assert len(res) == 0
#             res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'State': 'Allocated', 'ModelName': 'nvidia-k2',
#                                                             'SubregionNames': self.region_name_2}).response.FlexibleGpus
#             assert len(res) == 0
#             res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'State': 'Allocated', 'ModelName': 'nvidia-m60',
#                                                             'SubregionNames': self.region_name_2}).response.FlexibleGpus
#             assert len(res) == 0
        except OscApiException as error:
            raise error
        finally:
            if not self.res_link_1:
                self.res_link_1 = self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=self.gpus_id_1, VmId=self.inst_info_1[INSTANCE_ID_LIST][0])
                wait_flexible_gpu_state(self.a1_r1, [self.gpus_id_1], state="attaching")

    def test_T4230_filters_subregions(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'SubregionNames': [self.region_name_1]}).response.FlexibleGpus
        assert len(res) == 2

    def test_T4231_filters_incorrect_type(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        try:
            self.a1_r1.oapi.ReadFlexibleGpus(Filters=['ModelNames', 'nvidia-m60'])
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T4232_none_filter(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        try:
            self.a1_r1.oapi.ReadFlexibleGpus(Filters={None: None}).response.FlexibleGpus
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T4233_filters_model_name_non_existent(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        try:
            self.a1_r1.oapi.ReadFlexibleGpus(Filters={'other': ['nvidia-k2']})
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T4234_without_filters(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        ret.check_response()

    def test_T4235_dry_run(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        res = self.a1_r1.oapi.ReadFlexibleGpus(DryRun=True)
        assert_dry_run(res)

    def test_T5098_with_generations_filters(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'Generations': ['v4']}).response.FlexibleGpus
        assert len(res) == 2

    def test_T5099_with_invalid_generations_filters(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        res = self.a1_r1.oapi.ReadFlexibleGpus(Filters={'Generations': ['toto']}).response.FlexibleGpus
        assert len(res) == 0

    def test_T5100_with_incorrect_generations_type_filters(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        try:
            self.a1_r1.oapi.ReadFlexibleGpus(Filters={'Generations': 'v4'}).response.FlexibleGpus
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    @pytest.mark.tag_sec_confidentiality
    def test_T5101_with_other_account_generations_filters(self):
        if self.insufficient_capacity:
            pytest.skip("not enough capacity on fgpu")
        if not self.single_account:
            res = self.a2_r1.oapi.ReadFlexibleGpus(Filters={'Generations': ['v4']}).response.FlexibleGpus
            assert len(res) == 1
