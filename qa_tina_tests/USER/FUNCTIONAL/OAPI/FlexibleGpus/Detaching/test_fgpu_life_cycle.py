from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_tina_tools.tools.tina.wait_tools import wait_flexible_gpu_state
from qa_tina_tests.USER.FUNCTIONAL.OAPI.FlexibleGpus import fgpu_life_cycle
from qa_tina_tests.USER.FUNCTIONAL.OAPI.FlexibleGpus.fgpu_life_cycle import FgpuLifeCycle


class Test_fgpu_life_cycle(FgpuLifeCycle):


    def test_T4308_detaching_ready(self):
        self.init_test(state=6, istate2='ready')
        # TODO check if gpu should be available
        self.check_gpu_instance(total_gpu=1, vcores=fgpu_life_cycle.CORE_NUM, memory_ram=fgpu_life_cycle.RAM_NUM)
        self.check_gpu_fgpu_status(gpu_in_use=1, reserved_fgpu=1, fgpu_state='detaching')

    def test_T4297_detaching_terminate_dovd(self):
        self.init_test(state=6, delete_on_vm_deletion=True, terminate=True)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], cleanup=True)  # replace with wait
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=0)

    def test_T4298_detaching_terminate_ndovd(self):
        self.init_test(state=6, terminate=True)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='allocated')
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=1, fgpu_state='allocated')

    def test_T4299_detaching_stop(self):
        self.init_test(state=6, stop=True)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='allocated')
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=1, fgpu_state='allocated')

    def test_T4300_detaching_link(self):
        self.init_test(state=6)
        self.a1_r1.oapi.LinkFlexibleGpu(VmId=self.vm_id, FlexibleGpuId=self.fgpu_id)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='attached')
        self.check_gpu_fgpu_status(gpu_in_use=1, reserved_fgpu=1, fgpu_state='attached')

    def test_T4301_detaching_unlink(self):
        self.init_test(state=6)
        self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=self.fgpu_id)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='detaching')
        self.check_gpu_fgpu_status(gpu_in_use=1, reserved_fgpu=1, fgpu_state='detaching')

    def test_T4302_detaching_delete(self):
        self.init_test(state=6)
        try:
            self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=self.fgpu_id)
            self.fgpu_id = None
            assert False, 'Should not be successful'
        except OscApiException as error:
            assert_error(error, 409, '6003', 'InvalidState')
        self.check_gpu_fgpu_status(gpu_in_use=1, reserved_fgpu=1, fgpu_state='detaching')
