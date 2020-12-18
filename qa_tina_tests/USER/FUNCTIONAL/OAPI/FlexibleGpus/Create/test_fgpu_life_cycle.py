from qa_tina_tests.USER.FUNCTIONAL.OAPI.FlexibleGpus.fgpu_life_cycle import Fgpu_life_cycle
from qa_tina_tests.USER.FUNCTIONAL.OAPI.FlexibleGpus import fgpu_life_cycle
import pytest
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_error
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_flexible_gpu_state
from qa_tina_tools.tina import oapi, info_keys, wait
from qa_test_tools.config import config_constants as constants
from qa_common_tools.ssh import SshTools
from qa_test_tools.test_base import known_error

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

    def test_T5030_with_tina_1fgpu_update_type_to_other_tina_type_with_different_genaration(self):
        try:
            ret = self.a1_r1.intel.pci.find_gpu_reservations()
            if self.max_fgpu - len(ret.response.result) < 2:
                pytest.skip("not enough capacity on fgpu")
            ret = self.a1_r1.oapi.ReadFlexibleGpus()
            num_fgpu = len(ret.response.FlexibleGpus)
            self.init_test(4)
            ret = self.a1_r1.oapi.ReadFlexibleGpus()
            assert len(ret.response.FlexibleGpus) == num_fgpu + 1
            self.a1_r1.oapi.UpdateVm(VmId=self.vm_id, VmType='tinav3.c2r4')
        except OscApiException as error:
            assert_error(error, 409, '9072', 'ResourceConflict')

    def test_T5058_link_fgpu_to_starting_stopped_vm(self):
        vm_info = None
        gpu_id = None
        gpu_linked = False
        try:
            vm_info = oapi.create_Vms(self.a1_r1, state='stopped', vm_type=self.a1_r1.config.region.get_info(
                                                         constants.DEFAULT_GPU_INSTANCE_TYPE))
            kp_path = vm_info[info_keys.KEY_PAIR][info_keys.PATH]
            gpu_id = self.a1_r1.oapi.CreateFlexibleGpu(
                ModelName=self.a1_r1.config.region.get_info(constants.DEFAULT_GPU_MODEL_NAME),
                SubregionName=self.a1_r1.config.region.az_name). \
                response.FlexibleGpu.FlexibleGpuId
            wait.wait_FlexibleGpus_state(self.a1_r1, [gpu_id], state='allocated')
            self.a1_r1.oapi.LinkFlexibleGpu(FlexibleGpuId=gpu_id,
                                            VmId=vm_info[info_keys.VM_IDS][0])
            wait.wait_FlexibleGpus_state(self.a1_r1, [gpu_id], state='attached')
            gpu_linked = True
            oapi.start_Vms(self.a1_r1, [vm_info[info_keys.VM_IDS][0]])
            wait.wait_Vms_state(self.a1_r1, [vm_info[info_keys.VM_IDS][0]], state='ready')
            vm_ip = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [vm_info[info_keys.VM_IDS][0]]}).response.Vms[0].PublicIp
            sshclient = SshTools.check_connection_paramiko(vm_ip, kp_path,
                                                           username=self.a1_r1.config.region.get_info(
                                                               constants.CENTOS_USER))
            cmd = 'sudo yum install pciutils -y'
            _, status, _ = SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=300)
            assert not status, "SSH command was not executed correctly on the remote host"
            cmd = 'sudo lspci | grep -c NVIDIA '
            out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
            assert not status, "SSH command was not executed correctly on the remote host"
            assert out == "1\r\n"
            assert False, 'Remove known error'
        except Exception:
            known_error('TINA-5375', 'fGPU not found in VM'),
        finally:
            if gpu_linked:
                oapi.stop_Vms(self.a1_r1, [vm_info[info_keys.VM_IDS][0]])
                self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=gpu_id)
                wait.wait_FlexibleGpus_state(self.a1_r1, [gpu_id], state='allocated')
            if gpu_id:
                self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=gpu_id)
                wait.wait_FlexibleGpus_state(self.a1_r1, [gpu_id], cleanup=True)
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
