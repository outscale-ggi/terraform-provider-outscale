

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_tina_tests.USER.FUNCTIONAL.OAPI.FlexibleGpus.fgpu_life_cycle import Fgpu_life_cycle
from qa_tina_tools.tools.tina.wait_tools import wait_flexible_gpu_state


class Test_fgpu_life_cycle(Fgpu_life_cycle):

    def test_T4278_allocated_link_running(self):
        # create, link, check
        self.init_test(state=2)
        self.a1_r1.oapi.LinkFlexibleGpu(VmId=self.vm_id, FlexibleGpuId=self.fgpu_id)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='attaching')
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=1, fgpu_state='attaching')

    def test_T4279_allocated_link_stopped(self):
        # create, link, check
        self.init_test(state=2, stop=True)
        self.a1_r1.oapi.LinkFlexibleGpu(VmId=self.vm_id, FlexibleGpuId=self.fgpu_id)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='attached')  # replace with wait
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=1, fgpu_state='attached')

    def test_T4280_allocated_unlink(self):
        # create, unlink, check error
        self.init_test(state=2)
        try:
            self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=self.fgpu_id)
            assert False, 'Call should have failed, not linked yet'
        except OscApiException as error:
            assert_error(error, 409, '6003', 'InvalidState')

    def test_T4281_allocated_delete(self):
        # create, delete, check
        self.init_test(state=2)
        self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=self.fgpu_id)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], cleanup=True)
        self.fgpu_id = None
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=0)
