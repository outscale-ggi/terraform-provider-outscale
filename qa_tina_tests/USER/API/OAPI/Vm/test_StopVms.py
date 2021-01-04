# -*- coding:utf-8 -*-
import pytest

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances
from qa_tina_tools.tools.tina.delete_tools import terminate_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_tina_tests.USER.API.OAPI.Vm.Vm import validate_vms_state_response


class Test_StopVms(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.info = None
        super(Test_StopVms, cls).setup_class()
        try:
            cls.info = create_instances(cls.a1_r1, nb=10)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.info:
                delete_instances(cls.a1_r1, cls.info)
        finally:
            super(Test_StopVms, cls).teardown_class()

    def test_T2112_without_ids(self):
        try:
            self.a1_r1.oapi.StopVms()
            assert False, 'Call without ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2113_with_empty_ids(self):
        try:
            self.a1_r1.oapi.StopVms(VmIds=[])
            assert False, 'Call without ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2114_with_invalid_ids(self):
        try:
            self.a1_r1.oapi.StopVms(VmIds=['foo'])
            assert False, 'Call with invalid ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2115_from_running(self):
        vm_id = self.info[INSTANCE_ID_LIST][0]
        ret = self.a1_r1.oapi.StopVms(VmIds=[vm_id]).response.Vms
        assert len(ret) == 1
        for vm in ret:
            validate_vms_state_response(vm, state={
                'VmId': vm_id,
                'PreviousState': 'running',
                'CurrentState': 'stopping',
            })
        # Instance maybe stays in shutting-down state, we force stop before cleanup
        self.a1_r1.oapi.StopVms(VmIds=[vm_id], ForceStop=True)
        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[vm_id], state='stopped')

    def test_T2116_from_running_with_force(self):
        vm_id = self.info[INSTANCE_ID_LIST][1]
        ret = self.a1_r1.oapi.StopVms(VmIds=[vm_id], ForceStop=True).response.Vms
        assert len(ret) == 1
        for vm in ret:
            validate_vms_state_response(vm, state={
                'VmId': vm_id,
                'PreviousState': 'running',
                'CurrentState': 'stopping',
            })
        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[vm_id], state='stopped')

    def test_T2117_from_running_with_invalid_force(self):
        vm_id = self.info[INSTANCE_ID_LIST][2]
        try:
            self.a1_r1.oapi.StopVms(VmIds=[vm_id], ForceStop='foo')
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4110')

    def test_T2118_from_ready(self):
        vm_id = self.info[INSTANCE_ID_LIST][3]
        wait_instances_state(self.a1_r1, instance_id_list=[vm_id], state='ready')
        ret = self.a1_r1.oapi.StopVms(VmIds=[vm_id]).response.Vms
        assert len(ret) == 1
        for vm in ret:
            validate_vms_state_response(vm, state={
                'VmId': vm_id,
                'PreviousState': 'running',
                'CurrentState': 'stopping',
            })
        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[vm_id], state='stopped')

    def test_T2119_from_stop(self):
        vm_id = self.info[INSTANCE_ID_LIST][4]
        self.a1_r1.fcu.StopInstances(InstanceId=[vm_id])
        ret = self.a1_r1.oapi.StopVms(VmIds=[vm_id]).response.Vms
        assert len(ret) == 1
        for vm in ret:
            validate_vms_state_response(vm, state={
                'VmId': vm_id,
                'PreviousState': 'stopping',
                'CurrentState': 'stopping',
            })
        # Instance maybe stays in shutting-down state, we force stop before cleanup
        self.a1_r1.oapi.StopVms(VmIds=[vm_id], ForceStop=True)
        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[vm_id], state='stopped')

    def test_T2120_from_stopped(self):
        vm_id = self.info[INSTANCE_ID_LIST][5]
        stop_instances(self.a1_r1, [vm_id])
        ret = self.a1_r1.oapi.StopVms(VmIds=[vm_id]).response.Vms
        assert len(ret) == 1
        for vm in ret:
            validate_vms_state_response(vm, state={
                'VmId': vm_id,
                'PreviousState': 'stopped',
                'CurrentState': 'stopped',
            })
        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[vm_id], state='stopped')

    def test_T2121_from_terminated(self):
        vm_id = self.info[INSTANCE_ID_LIST][5]
        terminate_instances(self.a1_r1, [vm_id])
        self.info[INSTANCE_ID_LIST].remove(vm_id)
        try:
            self.a1_r1.oapi.StopVms(VmIds=[vm_id])
            assert False, 'Call with terminated instance should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'InvalidState', '6003')

    def test_T2122_with_unknown_param(self):
        vm_id = self.info[INSTANCE_ID_LIST][6]
        try:
            self.a1_r1.oapi.StopVms(VmIds=[vm_id], foo='bar')
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameter', '3001')

    def test_T2123_with_unknown_ids(self):
        try:
            self.a1_r1.oapi.StopVms(VmIds=['i-12345678'])
            assert False, 'Call with invalid ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')

    @pytest.mark.tag_sec_confidentiality
    def test_T2124_with_instance_from_another_account(self):
        info = create_instances(self.a2_r1)
        try:
            self.a1_r1.oapi.StopVms(VmIds=info[INSTANCE_ID_LIST])
            assert False, 'Call with instance from another account should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')
        finally:
            delete_instances(self.a2_r1, info)

    def test_T2125_with_multiple_valid_instances(self):
        vm_ids = self.info[INSTANCE_ID_LIST][7:9]
        ret = self.a1_r1.oapi.StopVms(VmIds=vm_ids).response.Vms
        assert len(ret) == 2
        for vm in ret:
            validate_vms_state_response(vm, state={
                'PreviousState': 'running',
                'CurrentState': 'stopping',
            })
        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=vm_ids, state='stopped')

    def test_T2126_with_multiple_valid_and_invalid_instances(self):
        vm_id = self.info[INSTANCE_ID_LIST][9]
        try:
            self.a1_r1.oapi.StopVms(VmIds=[vm_id] + ['i-12345678'])
            assert False, 'Call with invalid instance should not have been successful'
        except OscApiException as error:
            wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[vm_id], state='running')
            assert_oapi_error(error, 400, 'InvalidResource', '5063')
