import pytest

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances, start_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances, terminate_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, INSTANCE_SET, KEY_PAIR, PATH
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.misc import assert_error, assert_oapi_error
from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants


from qa_tina_tools.tools.tina.wait_tools import wait_flexible_gpu_state

MODEL_NAME = 'nvidia-k2'
DEFAULT_TYPE = 'tinav4.c4r8'
CORE_NUM = 4
RAM_NUM = 8
GPU_TYPE = 'tinav4.c2r8p3'
GPU_TYPE_CORES = 2
GPU_TYPE_RAMS = 8


def check_gpu_instance(osc_sdk, inst_id, ip_address, key_path, user_name, logger, total_gpu, vcores, memory_ram):

    sshclient = SshTools.check_connection_paramiko(ip_address, key_path, user_name)
    ret = osc_sdk.intel.instance.find(id=inst_id)
    ret = osc_sdk.intel.device.find_server(name=ret.response.result[0].slots[0].server)
    assert len(ret.response.result) > 0
    cmd = 'sudo nproc'
    out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
    logger.info(out)
    assert not status, "SSH command was not executed correctly on the remote host"
    assert not vcores or out.strip() == str(vcores), "Amount of cores does not match specifications for this type of instances"
    cmd = "sudo dmidecode -t 16 | grep 'Maximum Capacity' | awk '{print $3}'"
    out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
    logger.info(out)
    assert not status, "SSH command was not executed correctly on the remote host"
    assert not memory_ram or out.strip() == str(memory_ram), "Memory does not match specifications for this type of instance"
    assert not status, "SSH command was not executed correctly on the remote host"
    # cmd = 'sudo lspci | grep -c NVIDIA'
    cmd = "sudo lshw -C display | grep -c '*-display:'"
    out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd, expected_status=-1)
    logger.info(out)
    err = total_gpu and out.split()[-1:][0].strip() != str(total_gpu + 1)
    assert not err, "The total GPU does not match "


class Test_fgpu_life_cycle(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'gpu_limit': 4}
        super(Test_fgpu_life_cycle, cls).setup_class()
        try:
            # get max fgpu available
            cls.max_fgpu = 4
        except Exception:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            ret = cls.a1_r1.intel.pci.read_flexible_gpus(owner_id=cls.a1_r1.config.account.account_id)
            for fgpu in ret.response.result.flexible_gpus:
                cls.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=fgpu.flexible_gpu.flexible_gpu_id)
        except:
            super(Test_fgpu_life_cycle, cls).teardown_class()

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        self.inst_info = None
        self.vm_id = None
        self.fgpu_id = None
        self.ret_link = None
        self.ret_unlink = None
        self.dovd = False
        ret = self.a1_r1.intel.pci.find(state='in-use')
        self.num_gpus = len(ret.response.result) if ret.response.result else 0

    def teardown_method(self, method):
        try:
            if self.inst_info:
                delete_instances(self.a1_r1, self.inst_info)
            if self.fgpu_id:
                if not self.dovd:
                    self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=self.fgpu_id)
                wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], cleanup=True)
        finally:
            OscTestSuite.teardown_method(self, method)

    def check_gpu_instance(self, total_gpu, vcores, memory_ram):
        check_gpu_instance(self.a1_r1,
                           self.inst_info[INSTANCE_ID_LIST][0],
                           self.inst_info[INSTANCE_SET][0]['ipAddress'],
                           self.inst_info[KEY_PAIR][PATH],
                           self.a1_r1.config.region.get_info(constants.CENTOS_USER),
                           self.logger,
                           total_gpu, vcores, memory_ram)

    def check_gpu_fgpu_status(self, gpu_in_use, reserved_fgpu, fgpu_state=None):

        # ret1 = self.a1_r1.intel.pci.find_gpu_reservations()
        # print(ret1.response.display())
        ret2 = self.a1_r1.intel.pci.read_flexible_gpus(owner_id=self.a1_r1.config.account.account_id)
        # print(ret2.response.display())
        ret3 = self.a1_r1.intel.pci.find(state='in-use')
        # print(ret3.response.display())

        num_fgpus = len(ret2.response.result.flexible_gpus) if ret2.response.result.flexible_gpus else 0
        num_used_gpus = len(ret3.response.result) if ret3.response.result else 0
        reserved_fgpu_error = (num_fgpus != reserved_fgpu)
        gpu_in_use_error = (num_used_gpus != gpu_in_use + self.num_gpus)

        states = set([fgpu.state for fgpu in ret2.response.result.flexible_gpus])
        fgpu_state_error = fgpu_state and (len(states) != 1 or fgpu_state not in states)

        if reserved_fgpu_error or gpu_in_use_error or fgpu_state_error:
            raise OscTestException('Unexpected value for number of in-use gpu/reserved fgpu ({} -> {}, {} -> {}) or fgpu state ({} -> {})'.format(gpu_in_use + self.num_gpus, num_used_gpus, reserved_fgpu, num_fgpus, fgpu_state, states))

    def init_test(self, state, inst_type=DEFAULT_TYPE, deleteOnVmDeletion=False, create=True, stop=False,
                  terminate=False, istate1='running', istate2='running', create_gpu=True):
        self.dovd = deleteOnVmDeletion
        try:
            if create:
                self.inst_info = create_instances(self.a1_r1, inst_type=inst_type, state=istate1)
                self.vm_id = self.inst_info[INSTANCE_ID_LIST][0]
            if state > 1 and create_gpu:
                # call intel update as Create call does not support DeleteOnVmDelete
                # self.a1_r1.oapi.CreateFlexibleGpu(DeleteOnVmDeletion=deleleOnVmDeletion, ModelName=MODEL_NAME, SubregionName=self.a1_r1.config.region.az_name)
                ret = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=MODEL_NAME, SubregionName=self.a1_r1.config.region.az_name)
                self.fgpu_id = ret.response.FlexibleGpu.FlexibleGpuId
                self.a1_r1.intel.pci.update_flexible_gpu(owner_id=self.a1_r1.config.account.account_id,
                                                         flexible_gpu_id=self.fgpu_id, delete_on_vm_deletion=deleteOnVmDeletion)
                wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='allocated')
            if state > 2:
                self.ret_link = self.a1_r1.oapi.LinkFlexibleGpu(VmId=self.vm_id, FlexibleGpuId=self.fgpu_id)
                wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='attaching')
            if state > 3:
                stop_instances(self.a1_r1, [self.vm_id])
                wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='attached')
            if state > 4:
                start_instances(self.a1_r1, [self.vm_id], state=istate2)
                ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vm_id]})
                self.inst_info[INSTANCE_SET][0]['ipAddress'] = ret.response.Vms[0].PublicIp  # ret.response.Vms[0].Nics[0].LinkPublicIp.PublicIp
            if state > 5:
                self.ret_unlink = self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=self.fgpu_id)
                wait_flexible_gpu_state(self.a1_r1, [self.fgpu_id], state='detaching')
            if stop:
                stop_instances(self.a1_r1, [self.vm_id])
            if terminate:
                terminate_instances(self.a1_r1, [self.vm_id])
        except Exception as err:
            if self.inst_info:
                try:
                    delete_instances(self.a1_r1, self.inst_info)
                except:
                    pass
            if not deleteOnVmDeletion and self.fgpu_id:
                try:
                    self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=self.fgpu_id)
                except:
                    pass
            self.inst_info = None
            self.fgpu_id = None
            raise err

    def test_T4274_gpu_instance(self):
        # create gpu instance
        self.init_test(state=1, inst_type=GPU_TYPE, istate1='ready')
        self.check_gpu_instance(total_gpu=1, vcores=GPU_TYPE_CORES, memory_ram=GPU_TYPE_RAMS)
        self.check_gpu_fgpu_status(gpu_in_use=1, reserved_fgpu=1, fgpu_state='attached')

    def test_T4275_gpu_instance_with_attached_fgpu(self):
        try:
            ret = self.a1_r1.intel.pci.find_gpu_reservations()
            if self.max_fgpu - len(ret.response.result) < 2:
                pytest.skip("not enough capacity on fgpu")
            # create gpu instance
            self.init_test(state=5, inst_type=GPU_TYPE, istate2='ready')
            self.check_gpu_instance(total_gpu=2, vcores=GPU_TYPE_CORES, memory_ram=GPU_TYPE_RAMS)
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
                fgpu_ids.append(self.a1_r1.oapi.CreateFlexibleGpu(ModelName=MODEL_NAME,
                                                                  SubregionName=self.a1_r1.config.region.az_name).response.FlexibleGpu.FlexibleGpuId)
            try:
                self.a1_r1.oapi.CreateFlexibleGpu(ModelName=MODEL_NAME, SubregionName=self.a1_r1.config.region.az_name)
                assert False, 'Call should have failed, not enough fgpus available'
            except OscApiException as error:
                assert_error(error, 400, '10046', 'TooManyResources (QuotaExceded)')
        except OscApiException as error:
            assert_error(error, 400, '10001', 'InsufficientCapacity')
        finally:
            for fgpu_id in fgpu_ids:
                self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=fgpu_id)

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
        self.check_gpu_instance(total_gpu=1, vcores=CORE_NUM, memory_ram=RAM_NUM)
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

    def test_T4308_detaching_ready(self):
        self.init_test(state=6, istate2='ready')
        # TODO check if gpu should be available
        self.check_gpu_instance(total_gpu=1, vcores=CORE_NUM, memory_ram=RAM_NUM)
        self.check_gpu_fgpu_status(gpu_in_use=1, reserved_fgpu=1, fgpu_state='detaching')

    def test_T4297_detaching_terminate_dovd(self):
        self.init_test(state=6, deleteOnVmDeletion=True, terminate=True)
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

    def test_T4408_with_aws_type_instance(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        num_fgpu = len(ret.response.FlexibleGpus)
        self.init_test(1, inst_type=GPU_TYPE)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1

    def test_T4409_with_aws_Vm_and_terminate_instance(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        num_fgpu = len(ret.response.FlexibleGpus)
        self.init_test(1, inst_type=GPU_TYPE)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1
        delete_instances(self.a1_r1, self.inst_info)
        self.inst_info = None
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu

    def test_T4410_with_aws_Vm_and_update_with_deleteonvmdelete_false(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        num_fgpu = len(ret.response.FlexibleGpus)
        self.init_test(1, inst_type=GPU_TYPE, create_gpu=False)
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
        self.a1_r1.oapi.UpdateVm(VmId=self.vm_id, VmType=GPU_TYPE)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1

    def test_T4412_with_tina_1fgpu_update_type_to_aws_1fgpu(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        num_fgpu = len(ret.response.FlexibleGpus)
        self.init_test(4)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1
        self.a1_r1.oapi.UpdateVm(VmId=self.vm_id, VmType=GPU_TYPE)
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
        fgpus = []
        try:
            ret = self.a1_r1.intel.pci.find_gpu_reservations()
            if self.max_fgpu - len(ret.response.result) < 2:
                pytest.skip("not enough capacity on fgpu")
            ret = self.a1_r1.oapi.ReadFlexibleGpus()
            num_fgpu = len(ret.response.FlexibleGpus)
            self.inst_info = create_instances(self.a1_r1, inst_type=DEFAULT_TYPE, state='ready')
            vm_id = self.inst_info[INSTANCE_ID_LIST][0]
            ret = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=MODEL_NAME, SubregionName=self.a1_r1.config.region.az_name)
            fgpu_id1 = ret.response.FlexibleGpu.FlexibleGpuId
            fgpus.append(fgpu_id1)
            ret1 = self.a1_r1.oapi.CreateFlexibleGpu(ModelName=MODEL_NAME, SubregionName=self.a1_r1.config.region.az_name)
            fgpu_id2 = ret1.response.FlexibleGpu.FlexibleGpuId
            fgpus.append(fgpu_id2)
            self.a1_r1.oapi.LinkFlexibleGpu(VmId=vm_id, FlexibleGpuId=fgpu_id1)
            self.a1_r1.oapi.LinkFlexibleGpu(VmId=vm_id, FlexibleGpuId=fgpu_id2)
            stop_instances(self.a1_r1, [vm_id])
            ret = self.a1_r1.oapi.ReadFlexibleGpus()
            assert len(ret.response.FlexibleGpus) == num_fgpu + 2
            self.a1_r1.oapi.UpdateVm(VmId=vm_id, VmType=GPU_TYPE)
            ret = self.a1_r1.oapi.ReadFlexibleGpus()
            assert len(ret.response.FlexibleGpus) >= 1
        finally:
            for fgpu in fgpus:
                self.a1_r1.oapi.UnlinkFlexibleGpu(FlexibleGpuId=fgpu)
                wait_flexible_gpu_state(self.a1_r1, [fgpu], state='allocated')
                self.a1_r1.oapi.DeleteFlexibleGpu(FlexibleGpuId=fgpu)
                wait_flexible_gpu_state(self.a1_r1, [fgpu], cleanup=True)

    def test_T4415_with_aws_1fgpu_and_update_type_to_tina(self):
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        num_fgpu = len(ret.response.FlexibleGpus)
        self.init_test(1, inst_type=GPU_TYPE)
        ret = self.a1_r1.oapi.ReadFlexibleGpus()
        assert len(ret.response.FlexibleGpus) == num_fgpu + 1
        stop_instances(self.a1_r1, [self.vm_id])
        self.a1_r1.oapi.UpdateVm(VmId=self.vm_id, VmType=DEFAULT_TYPE)
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
