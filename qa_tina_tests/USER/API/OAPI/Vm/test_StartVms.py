# -*- coding:utf-8 -*-
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tests.USER.API.OAPI.Vm.Vm import validate_vms_state_response
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import terminate_instances, delete_instances, stop_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


NUM_INST = 10


class Test_StartVms(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_StartVms, cls).setup_class()
        cls.inst_info = None
        cls.num_inst = 0
        try:
            cls.inst_info = create_instances(cls.a1_r1, nb=NUM_INST)
            cls.inst_info2 = create_instances(cls.a2_r1, nb=1)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
            if cls.inst_info2:
                delete_instances(cls.a2_r1, cls.inst_info2)
        finally:
            super(Test_StartVms, cls).teardown_class()

    def get_insts(self, num=1):
        tmp_num = self.__class__.num_inst
        if tmp_num + num <= NUM_INST:
            self.__class__.num_inst += num
            return tmp_num
        else:
            raise OscTestException('Could not provide instance, review test')

    def test_T2099_without_ids(self):
        try:
            self.a1_r1.oapi.StartVms()
            assert False, 'Call without ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2100_with_empty_ids(self):
        try:
            self.a1_r1.oapi.StartVms(VmIds=[])
            assert False, 'Call without ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2101_with_invalid_ids(self):
        try:
            self.a1_r1.oapi.StartVms(VmIds=['foo'])
            assert False, 'Call with invalid ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2102_from_running(self):
        inst_num = self.get_insts()
        inst_id_list = [self.inst_info[INSTANCE_ID_LIST][inst_num]]
        wait_instances_state(self.a1_r1, inst_id_list, state='running')
        ret = self.a1_r1.oapi.StartVms(VmIds=inst_id_list).response.Vms
        assert len(ret) == 1
        for vm in ret:
            validate_vms_state_response(vm, state={
                'VmId': inst_id_list[0],
                'PreviousState': 'running',
                'CurrentState': 'running',
            })

    def test_T2104_from_stop(self):
        inst_num = self.get_insts()
        inst_id_list = [self.inst_info[INSTANCE_ID_LIST][inst_num]]
        wait_instances_state(self.a1_r1, inst_id_list, state='running')
        try:
            self.a1_r1.fcu.StopInstances(InstanceId=inst_id_list, Force=False)
            self.a1_r1.oapi.StartVms(VmIds=inst_id_list)
        except OscApiException as error:
            assert_oapi_error(error, 409, 'InvalidState', '6003')

    def test_T2105_from_stopped(self):
        inst_num = self.get_insts()
        inst_id_list = [self.inst_info[INSTANCE_ID_LIST][inst_num]]
        wait_instances_state(self.a1_r1, inst_id_list, state='running')
        stop_instances(self.a1_r1, inst_id_list)
        vms = self.a1_r1.oapi.StartVms(VmIds=inst_id_list).response.Vms
        assert len(vms) == 1
        for inst in vms:
            assert inst.VmId in inst_id_list
            assert inst.PreviousState == 'stopped'
            assert inst.CurrentState == 'pending' or inst.CurrentState == 'running'

    def test_T2106_from_terminated(self):
        inst_num = self.get_insts()
        inst_id_list = [self.inst_info[INSTANCE_ID_LIST][inst_num]]
        wait_instances_state(self.a1_r1, inst_id_list, state='running')
        terminate_instances(self.a1_r1, inst_id_list)
        try:
            self.a1_r1.oapi.StartVms(VmIds=inst_id_list)
        except OscApiException as error:
            assert_oapi_error(error, 409, 'InvalidState', '6003')

    def test_T2107_with_unknown_param(self):
        inst_num = self.get_insts()
        inst_id_list = [self.inst_info[INSTANCE_ID_LIST][inst_num]]
        wait_instances_state(self.a1_r1, inst_id_list, state='running')
        try:
            self.a1_r1.oapi.StartVms(VmIds=inst_id_list, foo='bar')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T2108_with_unknown_ids(self):
        try:
            self.a1_r1.oapi.StartVms(VmIds=['i-12345678'])
            assert False, 'Call with invalid ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')

    @pytest.mark.tag_sec_confidentiality
    def test_T2109_with_instance_from_another_account(self):
        inst_id_list = [self.inst_info2[INSTANCE_ID_LIST][0]]
        wait_instances_state(self.a2_r1, inst_id_list, state='running')
        try:
            self.a1_r1.oapi.StartVms(VmIds=inst_id_list)
            assert False, 'Call with instance from another account should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')

    def test_T2103_from_ready(self):
        inst_num = self.get_insts()
        inst_id_list = [self.inst_info[INSTANCE_ID_LIST][inst_num]]
        wait_instances_state(self.a1_r1, inst_id_list, state='ready')
        ret = self.a1_r1.oapi.StartVms(VmIds=inst_id_list)
        assert len(ret.response.Vms) == len(inst_id_list)
        assert ret.response.Vms[0].VmId == inst_id_list[0]
        assert ret.response.Vms[0].PreviousState == 'running'
        assert ret.response.Vms[0].CurrentState == 'running'

    def test_T2110_with_multiple_valid_instances(self):
        inst_num = self.get_insts(num=2)
        inst_id_list = self.inst_info[INSTANCE_ID_LIST][inst_num:inst_num + 1]
        wait_instances_state(self.a1_r1, inst_id_list, state='ready')
        ret = self.a1_r1.oapi.StartVms(VmIds=inst_id_list)
        assert len(ret.response.Vms) == len(inst_id_list)
        for inst in ret.response.Vms:
            assert inst.VmId in inst_id_list
            assert inst.PreviousState == 'running'
            assert inst.CurrentState == 'pending' or inst.CurrentState == 'running'

    def test_T2111_with_multiple_valid_and_invalid_instances(self):
        inst_num = self.get_insts()
        inst_id_list = [self.inst_info[INSTANCE_ID_LIST][inst_num]]
        wait_instances_state(self.a1_r1, inst_id_list, state='ready')
        try:
            self.a1_r1.oapi.StartVms(VmIds=inst_id_list + ['i-12345678'])
            assert False, 'Call with invalid instance should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')
