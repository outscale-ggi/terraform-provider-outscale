import sys

from qa_tina_tests.USER.API.OAPI.Vm.Vm import create_vms
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import assert_oapi_error
from qa_sdk_common.exceptions.osc_exceptions import OscApiException

from qa_tina_tools.tools.tina.wait_tools import wait_flexible_gpu_state, \
    wait_instances_state


class Test_attach_fgpu(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'gpu_limit': 4}
        cls.GROUPS = ['PRODUCTION', 'NVIDIA']
        cls.vm_id = None
        cls.fgpu_id = None
        cls.ret_link = None
        cls.max_ram = None
        cls.max_cpu = None
        super(Test_attach_fgpu, cls).setup_class()
        cls.max_ram = sys.maxsize
        ret = cls.a1_r1.oapi.ReadFlexibleGpuCatalog()
        for i in ret.response.FlexibleGpuCatalog:
            if i.MaxRam < cls.max_ram and i.ModelName.startswith('nvidia-k'):
                cls.max_ram = i.MaxRam
                cls.max_cpu = i.MaxCpu
                model_fgpu_selected = i.ModelName
        ret = cls.a1_r1.oapi.CreateFlexibleGpu(ModelName=model_fgpu_selected, SubregionName=cls.a1_r1.config.region.az_name)
        cls.fgpu_id = ret.response.FlexibleGpu.FlexibleGpuId

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret_link:
                cls.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=cls.fgpu_id)
                wait_flexible_gpu_state(cls.a1_r1, [cls.fgpu_id], state='detaching')

            if cls.fgpu_id:
                cls.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=cls.fgpu_id)
                wait_flexible_gpu_state(cls.a1_r1, [cls.fgpu_id], cleanup=True)
        finally:
            super(Test_attach_fgpu, cls).teardown_class()

    def test_T4572_with_invalid_ram_size(self):
        try:
            _, self.vm_id = create_vms(self.a1_r1, VmType='tinav3.c8r{}'.format(self.max_ram + 1), state='running')
            wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='allocated')
            self.ret_link = self.a1_r1.oapi.LinkFlexibleGpu(VmId=self.vm_id[0], FlexibleGpuId=self.fgpu_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9072')
        finally:
            if self.vm_id:
                self.a1_r1.oapi.DeleteVms(VmIds=self.vm_id)
                wait_instances_state(self.a1_r1, self.vm_id, state='terminated')

    def test_T4583_with_invalid_cpu_version(self):
        try:
            _, self.vm_id = create_vms(self.a1_r1, VmType='tinav1.c5r6', state='running')
            self.ret_link = self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=self.fgpu_id, VmId=self.vm_id[0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9072')
        finally:
            if self.vm_id:
                self.a1_r1.oapi.DeleteVms(VmIds=self.vm_id)
                wait_instances_state(self.a1_r1, self.vm_id, state='terminated')

    def test_T4584_with_invalid_cpu_size(self):
        try:
            _, self.vm_id = create_vms(self.a1_r1, VmType='tinav3.c{}r10'.format(self.max_cpu + 1), state='running')
            self.ret_link = self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=self.fgpu_id, VmId=self.vm_id[0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9072')
        finally:
            if self.vm_id:
                self.a1_r1.oapi.DeleteVms(VmIds=self.vm_id)
                wait_instances_state(self.a1_r1, self.vm_id, state='terminated')
