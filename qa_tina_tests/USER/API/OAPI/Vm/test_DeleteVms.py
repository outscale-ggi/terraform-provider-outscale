
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances, terminate_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_tina_tests.USER.API.OAPI.Vm.Vm import validate_vms_state_response


class Test_DeleteVms(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteVms, cls).setup_class()
        cls.info = None
        cls.infouser2 = None
        cls.deleted_ids = []
        try:
            cls.info = create_instances(cls.a1_r1, nb=9, state='running')
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            # ret = cls.a1_r1.oapi.ReadVms(Filters={'VmIds': cls.info[INSTANCE_ID_LIST]}).response.Vms
            # cls.info[INSTANCE_ID_LIST] = [inst.VmId for inst in ret]
            # StateComments
            delete_instances(cls.a1_r1, cls.info)
        finally:
            super(Test_DeleteVms, cls).teardown_class()

    def test_T2042_without_ids(self):
        try:
            self.a1_r1.oapi.DeleteVms()
            assert False, 'Call without ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2043_with_empty_ids(self):
        try:
            self.a1_r1.oapi.DeleteVms(VmIds=[])
            assert False, 'Call without ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2044_with_invalid_ids(self):
        try:
            self.a1_r1.oapi.DeleteVms(VmIds=['foo'])
            assert False, 'Call with invalid ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    # def test_TXXX_from_running(self):
    #     self.info = create_instances(self.a1_r1, state='running')
    #     vm_ids = [inst.instanceId for inst in self.info[INSTANCE_SET]]
    #     ret = self.a1_r1.oapi.DeleteVms(VmIds=vm_ids).response.Vms
    #     assert len(ret.response.Vms) == len(vm_ids)
    #     assert ret.response.Vms[0].VmId == vm_ids[0]
    #     assert ret.response.Vms[0].PreviousState == 'running'
    #     assert ret.response.Vms[0].CurrentState == 'shutting-down'
    #     # Instance maybe stays in shutting-down state, we force stop before cleanup
    #     self.a1_r1.fcu.StopInstances(InstanceId=vm_ids, Force=True)
    #     wait_instances_state(self.a1_r1, vm_ids, state='terminated')
    #     del self.info

    def test_T2045_from_ready(self):
        vm_id = self.info[INSTANCE_ID_LIST][0]
        # instance créé en state running
        wait_instances_state(self.a1_r1, [vm_id], state='ready')
        ret = self.a1_r1.oapi.DeleteVms(VmIds=[vm_id]).response.Vms
        assert len(ret) == len([vm_id])
        for inst in ret:
            validate_vms_state_response(inst, state={
                'VmId': vm_id,
                'PreviousState': 'running',
                'CurrentState': 'shutting-down',
            })
        wait_instances_state(self.a1_r1, [vm_id], state='terminated')

    def test_T2046_from_stop(self):
        vm_id = self.info[INSTANCE_ID_LIST][1]
        self.a1_r1.fcu.StopInstances(InstanceId=[vm_id], Force=False)
        ret = self.a1_r1.oapi.DeleteVms(VmIds=[vm_id]).response.Vms
        for inst in ret:
            validate_vms_state_response(inst, state={
                'VmId': vm_id,
                'PreviousState': 'stopping',
                'CurrentState': 'shutting-down',
            })
        # Instance maybe stays in shutting-down state, we force stop before cleanup
        self.a1_r1.fcu.StopInstances(InstanceId=[vm_id], Force=True)
        wait_instances_state(self.a1_r1, [vm_id], state='terminated')

    def test_T2047_from_stopped(self):
        vm_id = self.info[INSTANCE_ID_LIST][2]
        stop_instances(self.a1_r1, [vm_id])
        ret = self.a1_r1.oapi.DeleteVms(VmIds=[vm_id]).response.Vms
        for inst in ret:
            validate_vms_state_response(inst, state={
                'VmId': vm_id,
                'PreviousState': 'stopped',
                'CurrentState': 'shutting-down',  # TODO: open a Bug and add known_error ?
            })
        wait_instances_state(self.a1_r1, [vm_id], state='terminated')

    def test_T2048_from_terminated(self):
        vm_id = self.info[INSTANCE_ID_LIST][3]
        terminate_instances(self.a1_r1, [vm_id])
        ret = self.a1_r1.oapi.DeleteVms(VmIds=[vm_id]).response.Vms
        for inst in ret:
            validate_vms_state_response(inst, state={
                'VmId': vm_id,
                'PreviousState': 'terminated',
                'CurrentState': 'terminated',
            })
        wait_instances_state(self.a1_r1, [vm_id], state='terminated')
        del self.info[INSTANCE_SET]

    def test_T2049_with_unknown_param(self):
        vm_id = self.info[INSTANCE_ID_LIST][4]
        try:
            self.a1_r1.oapi.DeleteVms(VmIds=[vm_id], foo='bar')
            assert False, 'Call with invalid ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T2050_with_unknown_ids(self):
        try:
            self.a1_r1.oapi.DeleteVms(VmIds=['i-12345678'])
            del self.info[INSTANCE_SET]
            assert False, 'Call with invalid ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')

    def test_T2052_with_multiple_valid_instances(self):
        vm_id = self.info[INSTANCE_ID_LIST][5:7]
        ret = self.a1_r1.oapi.DeleteVms(VmIds=vm_id).response.Vms
        for inst in ret:
            validate_vms_state_response(inst, state={
                'PreviousState': 'running',
                'CurrentState': 'shutting-down',
            })
        wait_instances_state(self.a1_r1, vm_id, state='terminated')

    def test_T2053_with_multiple_valid_and_invalid_instances(self):
        vm_id = self.info[INSTANCE_ID_LIST][7]
        try:
            self.a1_r1.oapi.DeleteVms(VmIds=[vm_id] + ['i-12345678'])
            assert False, 'Call with invalid instance should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')
            wait_instances_state(self.a1_r1, [vm_id], state='running', threshold=1)

    @pytest.mark.tag_sec_confidentiality
    def test_T2051_with_instance_from_another_account(self):
        self.infouser2 = create_instances(self.a2_r1)
        vm_ids = self.infouser2[INSTANCE_ID_LIST]
        try:
            self.a1_r1.oapi.DeleteVms(VmIds=vm_ids)
            assert False, 'Call with instance from another account should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')
        finally:
            delete_instances(self.a2_r1, self.infouser2)

    def test_T3038_deletion_protection_activated(self):
        vm_id = self.info[INSTANCE_ID_LIST][8]
        self.a1_r1.oapi.UpdateVm(DeletionProtection=True, VmId=vm_id)
        try:
            self.a1_r1.oapi.DeleteVms(VmIds=[vm_id])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'OperationNotSupported', '8018')
        self.a1_r1.oapi.UpdateVm(DeletionProtection=False, VmId=vm_id)
        self.a1_r1.oapi.DeleteVms(VmIds=[vm_id])
