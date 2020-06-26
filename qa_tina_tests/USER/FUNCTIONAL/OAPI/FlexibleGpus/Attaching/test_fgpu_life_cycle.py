from qa_tina_tests.USER.FUNCTIONAL.OAPI.FlexibleGpus.fgpu_life_cycle import Fgpu_life_cycle
from qa_tina_tools.tools.tina.wait_tools import wait_flexible_gpu_state
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error

class Test_fgpu_life_cycle(Fgpu_life_cycle):


    def test_T4282_attaching_terminate_dovd(self):
        # create(dovd=True), link, terminate vm, check
        self.init_test(state=3, deleteOnVmDeletion=True, terminate=True)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], cleanup=True)
        self.fgpu_id = None
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=0)

    def test_T4283_attaching_terminate_ndovd(self):
        # create(dovd=False, link, terminate vm, check
        self.init_test(state=3, terminate=True)
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=1, fgpu_state='allocated')

    def test_T4284_attaching_stop(self):
        # create, link, stop
        self.init_test(state=3, stop=True)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='attached')
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=1, fgpu_state='attached')

    def test_T4285_attaching_unlink(self):
        # create, link, unlink, check
        self.init_test(state=3)
        self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=self.fgpu_id)
        wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='allocated')  # replace with wait
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=1, fgpu_state='allocated')

    def test_T4286_attaching_link(self):
        # create, link, link, check
        self.init_test(state=3)
        self.a1_r1.oapi.LinkFlexibleGpu(VmId=self.vm_id, FlexibleGpuId=self.fgpu_id)
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=1, fgpu_state='attaching')

    def test_T4287_attaching_delete(self):
        # create, link, delete, check
        self.init_test(state=3)
        try:
            self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=self.fgpu_id)
            self.fgpu_id = None
            assert False, 'Should not be successful'
        except OscApiException as error:
            assert_error(error, 409, '6003', 'InvalidState')
        self.check_gpu_fgpu_status(gpu_in_use=0, reserved_fgpu=1, fgpu_state='attaching')
