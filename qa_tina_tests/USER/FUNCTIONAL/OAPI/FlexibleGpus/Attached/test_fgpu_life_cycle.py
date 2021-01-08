from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_tina_tests.USER.FUNCTIONAL.OAPI.FlexibleGpus import fgpu_life_cycle
from qa_tina_tests.USER.FUNCTIONAL.OAPI.FlexibleGpus.fgpu_life_cycle import Fgpu_life_cycle
from qa_tina_tools.tools.tina.wait_tools import wait_flexible_gpu_state


class Test_fgpu_life_cycle(Fgpu_life_cycle):

    def test_T4288_attached_terminate_dovd(self):
        # create, link, delete, check
        self.init_test(state=4, terminate=True, deleteOnVmDeletion=True)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], cleanup=True)
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=0)

    def test_T4289_attached_terminate_ndovd(self):
        self.init_test(state=4, terminate=True)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='allocated')
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=1, fgpu_state='allocated')

    def test_T4304_attached_ready(self):
        self.init_test(state=5, istate2='ready')
        self.check_gpu_instance(total_gpu=1, vcores=fgpu_life_cycle.CORE_NUM, memory_ram=fgpu_life_cycle.RAM_NUM)
        # TODO check if gpu should be available
        self.check_gpu_fgpu_status(gpu_in_use=1, reserved_fgpu=1, fgpu_state='attached')

    def test_T4291_attached_stopped_unlink(self):
        self.init_test(state=4)
        self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=self.fgpu_id)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='allocated')
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=1, fgpu_state='allocated')

    def test_T4292_attached_running_unlink(self):
        self.init_test(state=5, istate2='running')
        self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=self.fgpu_id)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='detaching')
        self.check_gpu_fgpu_status(gpu_in_use=1, reserved_fgpu=1, fgpu_state='detaching')

    def test_T4293_attached_stopped_link(self):
        self.init_test(state=4)
        try:
            self.a1_r1.oapi.LinkFlexibleGpu(VmId=self.vm_id, FlexibleGpuId=self.fgpu_id)
            assert False, 'Should not be successful'
        except OscApiException as error:
            assert_error(error, 409, '6003', 'InvalidState')
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=1, fgpu_state='attached')

    def test_T4294_attached_running_link(self):
        self.init_test(state=5)
        try:
            self.a1_r1.oapi.LinkFlexibleGpu(VmId=self.vm_id, FlexibleGpuId=self.fgpu_id)
            assert False, 'Should not be successful'
        except OscApiException as error:
            assert_error(error, 409, '6003', 'InvalidState')
        self.check_gpu_fgpu_status(gpu_in_use=1, reserved_fgpu=1, fgpu_state='attached')

    def test_T4295_attached_stopped_delete(self):
        self.init_test(state=4)
        try:
            self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=self.fgpu_id)
            self.fgpu_id = None
            assert False, 'Should not be successful'
        except OscApiException as error:
            assert_error(error, 409, '6003', 'InvalidState')
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=1, fgpu_state='attached')

    def test_T4296_attached_running_delete(self):
        self.init_test(state=5)
        try:
            self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=self.fgpu_id)
            self.fgpu_id = None
            assert False, 'Should not be successful'
        except OscApiException as error:
            assert_error(error, 409, '6003', 'InvalidState')
        self.check_gpu_fgpu_status(gpu_in_use=1, reserved_fgpu=1, fgpu_state='attached')
