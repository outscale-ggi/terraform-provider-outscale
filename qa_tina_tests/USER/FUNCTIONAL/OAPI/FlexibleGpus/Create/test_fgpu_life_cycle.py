from qa_tina_tests.USER.FUNCTIONAL.OAPI.FlexibleGpus.fgpu_life_cycle import Fgpu_life_cycle
from qa_tina_tests.USER.FUNCTIONAL.OAPI.FlexibleGpus import fgpu_life_cycle
import pytest
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_error
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_flexible_gpu_state

class Test_fgpu_life_cycle(Fgpu_life_cycle):


    def test_T4274_gpu_instance(self):
        # create gpu instance
        self.init_test(state=1, inst_type=fgpu_life_cycle.GPU_TYPE, istate1='ready')
        self.check_gpu_instance(total_gpu=1, vcores=fgpu_life_cycle.GPU_TYPE_CORES, memory_ram=fgpu_life_cycle.GPU_TYPE_RAMS)
        self.check_gpu_fgpu_status(gpu_in_use=1, reserved_fgpu=1, fgpu_state='attached')

    def test_T4275_gpu_instance_with_attached_fgpu(self):
        try:
            ret = self.a1_r1.intel.pci.find_gpu_reservations()
            if self.max_fgpu - len(ret.response.result) < 2:
                pytest.skip("not enough capacity on fgpu")
            # create gpu instance
            self.init_test(state=5, inst_type=fgpu_life_cycle.GPU_TYPE, istate2='ready')
            self.check_gpu_instance(total_gpu=2, vcores=fgpu_life_cycle.GPU_TYPE_CORES, memory_ram=fgpu_life_cycle.GPU_TYPE_RAMS)
            self.check_gpu_fgpu_status(gpu_in_use=2, reserved_fgpu=2, fgpu_state='attached')
        except OscApiException as err:
            assert_oapi_error(err, 409, 'ResourceConflict', '9072')
    # add error (?) cases , link fgpu to gpu instance

    def test_T4276_create_fgpu(self):
        # create, check
        self.init_test(state=2, create=False)
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=1, fgpu_state='allocated')

    def test_T4277_create_fgpu_ic(self):
        fgpu_ids = []
        # create to many fgpus, check error
        try:
            for _ in range(self.max_fgpu):
                fgpu_ids.append(self.a1_r1.oapi.CreateFlexibleGpu(ModelName=fgpu_life_cycle.MODEL_NAME,
                                                                  SubregionName=self.a1_r1.config.region.az_name).response.FlexibleGpu.FlexibleGpuId)
            try:
                self.a1_r1.oapi.CreateFlexibleGpu(ModelName=fgpu_life_cycle.MODEL_NAME, SubregionName=self.a1_r1.config.region.az_name)
                assert False, 'Call should have failed, not enough fgpus available'
            except OscApiException as error:
                assert_error(error, 400, '10046', 'TooManyResources (QuotaExceded)')
        except OscApiException as error:
            assert_error(error, 400, '10001', 'InsufficientCapacity')
        finally:
            for fgpu_id in fgpu_ids:
                self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=fgpu_id)

    def test_T4408_with_aws_type_instance(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        num_fgpu = len(ret.response.FlexibleGpus)
        self.init_test(1, inst_type=fgpu_life_cycle.GPU_TYPE)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1

    def test_T4409_with_aws_Vm_and_terminate_instance(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        num_fgpu = len(ret.response.FlexibleGpus)
        self.init_test(1, inst_type=fgpu_life_cycle.GPU_TYPE)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1
        delete_instances(self.a1_r1, self.inst_info)
        self.inst_info = None
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu

    def test_T4410_with_aws_Vm_and_update_with_deleteonvmdelete_false(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        num_fgpu = len(ret.response.FlexibleGpus)
        self.init_test(1, inst_type=fgpu_life_cycle.GPU_TYPE, create_gpu=False)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        self.fgpu_id = ret.response.FlexibleGpus[0].FlexibleGpuId
        self.a1_r1.oapi.UpdateFlexibleGpu(FlexibleGpuId=self.fgpu_id, DeleteOnVmDeletion=False)
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1
        delete_instances(self.a1_r1, self.inst_info)
        self.inst_info = None
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1

    def test_T4411_with_tina_type_update_type_to_aws_1fgpu(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        num_fgpu = len(ret.response.FlexibleGpus)
        self.init_test(1)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu
        stop_instances(self.a1_r1, [self.vm_id])
        self.a1_r1.oapi.UpdateVm(VmId=self.vm_id, VmType=fgpu_life_cycle.GPU_TYPE)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1

    def test_T4412_with_tina_1fgpu_update_type_to_aws_1fgpu(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        num_fgpu = len(ret.response.FlexibleGpus)
        self.init_test(4)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1
        self.a1_r1.oapi.UpdateVm(VmId=self.vm_id, VmType=fgpu_life_cycle.GPU_TYPE)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 2

    def test_T4413_with_tina_1fgpu_update_type_to_aws_2fgpu(self):
        ret = self.a1_r1.intel.pci.find_gpu_reservations()
        if self.max_fgpu - len(ret.response.result) < 2:
            pytest.skip("not enough capacity on fgpu")
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        num_fgpu = len(ret.response.FlexibleGpus)
        self.init_test(4)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1
        self.a1_r1.oapi.UpdateVm(VmId=self.vm_id, VmType='og4.2xlarge')
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) >= 2

    def test_T4414_with_tina_2fgpu_update_type_to_aws_1fgpu(self):
        try:
            ret = self.a1_r1.intel.pci.find_gpu_reservations()
            if self.max_fgpu - len(ret.response.result) < 2:
                pytest.skip("not enough capacity on fgpu")
            ret = self.a1_r1.oapi.ReadFlexibleGpus()
            num_fgpu = len(ret.response.FlexibleGpus)
            self.inst_info = create_instances(self.a1_r1, inst_type=fgpu_life_cycle.DEFAULT_TYPE, state='ready')
            vm_id = self.inst_info[INSTANCE_ID_LIST][0]
            ret = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=fgpu_life_cycle.MODEL_NAME, SubregionName=self.a1_r1.config.region.az_name)
            fgpu_id1 = ret.response.FlexibleGpu.FlexibleGpuId
            ret1 = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=fgpu_life_cycle.MODEL_NAME, SubregionName=self.a1_r1.config.region.az_name)
            fgpu_id2 = ret1.response.FlexibleGpu.FlexibleGpuId
            self.a1_r1.oapi.LinkFlexibleGpu(VmId=vm_id, FlexibleGpuId=fgpu_id1)
            self.a1_r1.oapi.LinkFlexibleGpu(VmId=vm_id, FlexibleGpuId=fgpu_id2)
            stop_instances(self.a1_r1, [vm_id])
            ret = self.a1_r1.oapi.ReadFlexibleGpus()
            assert len(ret.response.FlexibleGpus) == num_fgpu + 2
            self.a1_r1.oapi.UpdateVm(VmId=vm_id, VmType=fgpu_life_cycle.GPU_TYPE)
            ret = self.a1_r1.oapi.ReadFlexibleGpus()
            assert len(ret.response.FlexibleGpus) >= 1
        except Exception as error:
            raise error
        finally:
            fgpus = self.a1_r1.oapi.ReadFlexibleGpus().response.FlexibleGpus
            for fgpu in fgpus:
                if fgpu.State != 'allocated':
                    self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=fgpu.FlexibleGpuId)
                    wait_flexible_gpu_state(self.a1_r1, [fgpu.FlexibleGpuId], state='allocated')
                self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=fgpu.FlexibleGpuId)
                wait_flexible_gpu_state(self.a1_r1, [fgpu.FlexibleGpuId], cleanup=True)

    def test_T4415_with_aws_1fgpu_and_update_type_to_tina(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        num_fgpu = len(ret.response.FlexibleGpus)
        self.init_test(1, inst_type=fgpu_life_cycle.GPU_TYPE)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1
        stop_instances(self.a1_r1, [self.vm_id])
        self.a1_r1.oapi.UpdateVm(VmId=self.vm_id, VmType=fgpu_life_cycle.DEFAULT_TYPE)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu

    def test_T4568_with_tina_1fgpu_update_type_to_other_tina_type(self):
        ret = self.a1_r1.intel.pci.find_gpu_reservations()
        if self.max_fgpu - len(ret.response.result) < 2:
            pytest.skip("not enough capacity on fgpu")
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        num_fgpu = len(ret.response.FlexibleGpus)
        self.init_test(4)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1
        self.a1_r1.oapi.UpdateVm(VmId=self.vm_id, VmType='tinav4.c2r4')
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1
