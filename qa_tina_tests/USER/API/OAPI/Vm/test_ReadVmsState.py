# -*- coding:utf-8 -*-
import pytest

from qa_test_tools.test_base import OscTestSuite
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_test_tools.misc import assert_oapi_error, assert_dry_run


class Test_ReadVmsState(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadVmsState, cls).setup_class()
        cls.info = None
        try:
            cls.info = create_instances(cls.a1_r1, nb=3, state='running')
            cls.a1_r1.oapi.StopVms(VmIds=[cls.info[INSTANCE_SET][2]['instanceId']], ForceStop=True)
            cls.a1_r1.oapi.DeleteVms(VmIds=[cls.info[INSTANCE_SET][2]['instanceId']])
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
            delete_instances(cls.a1_r1, cls.info)
        finally:
            super(Test_ReadVmsState, cls).teardown_class()
        cls.info = None

    def test_T2071_no_param(self):
        ret = self.a1_r1.oapi.ReadVmsState()
        # check if all are running
        assert len(ret.response.VmStates) == 2
        assert ret.response.VmStates[0].VmState == 'running', "State of the vm should be running"
        assert ret.response.VmStates[1].VmState == 'running', "State of the vm should be running"

    def test_T2072_include_all_vms_true(self):
        ret = self.a1_r1.oapi.ReadVmsState(AllVms=True)
        assert len(ret.response.VmStates) == 3

    def test_T2073_include_all_vms_false(self):
        ret = self.a1_r1.oapi.ReadVmsState(AllVms=False)
        # check if all are running
        for i in range(2):
            assert ret.response.VmStates[i].VmState == 'running', "State of the vm should be running"
        # check size of the list
        assert len(ret.response.VmStates) == 2


    def test_T2074_with_vm_id(self):
        result = self.a1_r1.oapi.ReadVmsState(Filters={'VmIds': [self.info[INSTANCE_SET][0]['instanceId']]})
        assert len(result.response.VmStates) == 1

    def test_T2075_with_vm_ids(self):
        ret = self.a1_r1.oapi.ReadVmsState(Filters={'VmIds': [self.info[INSTANCE_SET][0]['instanceId'],
                                                              self.info[INSTANCE_SET][1]['instanceId']]})
        assert len(ret.response.VmStates) == 2
        assert True if self.info[INSTANCE_SET][0]['instanceId'] in (vm.VmId for vm in ret.response.VmStates) else False
        assert True if self.info[INSTANCE_SET][1]['instanceId'] in (vm.VmId for vm in ret.response.VmStates) else False

    def test_T2076_filter_vm_state_name(self):
        # check running
        code_Name = 'running'
        ret = self.a1_r1.oapi.ReadVmsState(Filters={'VmStates': [code_Name]})
        assert ret.status_code == 200, ret.response.display()
        assert len(ret.response.VmStates) == 2
        for i in range(len(ret.response.VmStates)):
            assert ret.response.VmStates[i].VmState == code_Name
        # check terminated
        code_Name = 'terminated'
        ret = self.a1_r1.oapi.ReadVmsState(Filters={'VmStates': [code_Name]})
        assert len(ret.response.VmStates) == 0
        # check terminated with AllVms Activated
        code_Name = 'terminated'
        ret = self.a1_r1.oapi.ReadVmsState(AllVms=True, Filters={'VmStates': [code_Name]})
        assert len(ret.response.VmStates) == 1
        assert ret.response.VmStates[0].VmState == code_Name

    def test_T2077_multiple_filters(self):
        result = self.a1_r1.oapi.ReadVmsState(Filters={'VmIds': [self.info[INSTANCE_SET][0]['instanceId']],
                                                       'VmStates': ['running']})
        assert len(result.response.VmStates) == 1

    def test_T2078_invalid_filter_availability_zone(self):
        filter_dict = {'SubregionNames': ['Some-region-non-existing']}
        ret = self.a1_r1.oapi.ReadVmsState(Filters=filter_dict)
        assert len(ret.response.VmStates) == 0

    def test_T2083_invalid_filter_vm_state_name(self):
        try:
            ret = self.a1_r1.oapi.ReadVmsState(Filters={'VmStates': ['foo']})  # Code expected not name
            assert len(ret.response.VmStates) == 0
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T2084_with_invalid_vm_id(self):
        vm_id = 'foo'
        try:
            self.a1_r1.oapi.ReadVmsState(Filters={'VmIds': [vm_id]})
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2085_with_unknown_vm_id(self):
        vm_id = 'i-12345678'
        ret = self.a1_r1.oapi.ReadVmsState(Filters={'VmIds': [vm_id]})
        assert len(ret.response.VmStates) == 0

    def test_T3426_dry_run(self):
        ret = self.a1_r1.oapi.ReadVmsState(DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3427_other_account(self):
        ret = self.a2_r1.oapi.ReadVmsState().response.VmStates
        assert not ret

    @pytest.mark.tag_sec_confidentiality
    def test_T3428_other_account_with_filter(self):
        ret = self.a2_r1.oapi.ReadVmsState(Filters={'VmIds': self.info[INSTANCE_ID_LIST]}).response.VmStates
        assert not ret
