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
GPU_TYPE = 'og4.xlarge'
GPU_TYPE_CORES = 8
GPU_TYPE_RAMS = 61


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


class Fgpu_life_cycle(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'gpu_limit': 4}
        super(Fgpu_life_cycle, cls).setup_class()
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
            super(Fgpu_life_cycle, cls).teardown_class()

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
