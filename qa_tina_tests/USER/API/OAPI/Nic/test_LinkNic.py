# -*- coding:utf-8 -*-
import pytest

from qa_tina_tests.USER.API.OAPI.Nic.Nic import Nic
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


class Test_LinkNic(Nic):

    @classmethod
    def setup_class(cls):
        super(Test_LinkNic, cls).setup_class()
        cls.nic_id = None
        cls.nic_id2 = None
        cls.nic_id3 = None
        cls.nic_id4 = None
        cls.nic_id5 = None
        cls.nic_id6 = None
        cls.inst_info = None
        try:
            cls.vpc_inst_info = create_instances(cls.a1_r1, 7, state=None, subnet_id=cls.subnet_id1, sg_id_list=[cls.firewall_id1])
            cls.inst_info = create_instances(cls.a1_r1, 6, state=None)
            cls.nic_id = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic.NicId
            cls.nic_id2 = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic.NicId
            cls.nic_id3 = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic.NicId
            cls.nic_id4 = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic.NicId
            cls.nic_id5 = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic.NicId
            cls.nic_id6 = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic.NicId
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.nic_id:
                try:
                    cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id)
                except:
                    pass
            if cls.nic_id2:
                try:
                    cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id2)
                except:
                    pass
            if cls.nic_id3:
                try:
                    cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id3)
                except:
                    pass
            if cls.nic_id4:
                try:
                    cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id4)
                except:
                    pass
            if cls.nic_id5:
                try:
                    cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id5)
                except:
                    pass
            if cls.nic_id6:
                try:
                    cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id6)
                except:
                    pass
            if cls.inst_info:
                try:
                    delete_instances(cls.a1_r1, cls.inst_info)
                except:
                    pass
            if cls.vpc_inst_info:
                try:
                    delete_instances(cls.a1_r1, cls.vpc_inst_info)
                except:
                    pass
        finally:
            super(Test_LinkNic, cls).teardown_class()

    def setup_method(self, method):
        self.nic_link_id = None
        self.nic_link_id2 = None
        super(Test_LinkNic, self).setup_method(method)

    def teardown_method(self, method):
        try:
            if self.nic_link_id:
                self.a1_r1.oapi.UnlinkNic(LinkNicId=self.nic_link_id)

            if self.nic_link_id2:
                self.a1_r1.oapi.UnlinkNic(LinkNicId=self.nic_link_id2)

        finally:
            super(Test_LinkNic, self).teardown_method(method)

    def test_T2658_valid_case(self):
        vm_ids = [self.vpc_inst_info[INSTANCE_ID_LIST][0]]
        wait_instances_state(self.a1_r1, vm_ids, state='running')
        self.nic_link_id = self.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId=vm_ids[0], NicId=self.nic_id).response.LinkNicId
        assert self.nic_link_id.startswith('eni-attach-')

    def test_T2659_link_2_nic_on_same_vm(self):
        vm_ids = [self.vpc_inst_info[INSTANCE_ID_LIST][1]]
        wait_instances_state(self.a1_r1, vm_ids, state='running')
        self.nic_link_id = self.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId=vm_ids[0], NicId=self.nic_id2).response.LinkNicId
        try:
            self.nic_link_id2 = self.a1_r1.oapi.LinkNic(DeviceNumber=2, VmId=vm_ids[0], NicId=self.nic_id3).response.LinkNicId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'TooManyResources (QuotaExceded)', '10015')

    def test_T2660_link_on_same_device_number(self):
        vm_ids = [self.vpc_inst_info[INSTANCE_ID_LIST][2]]
        wait_instances_state(self.a1_r1, vm_ids, state='running')
        self.nic_link_id = self.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId=vm_ids[0], NicId=self.nic_id4).response.LinkNicId
        assert self.nic_link_id.startswith('eni-attach-')
        try:
            self.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId=vm_ids[0], NicId=self.nic_id5)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'TooManyResources (QuotaExceded)', '10015')

    def test_T2661_link_on_2_different_vm(self):
        vm_ids = self.vpc_inst_info[INSTANCE_ID_LIST][3:5]
        wait_instances_state(self.a1_r1, vm_ids, state='running')
        self.nic_link_id = self.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId=vm_ids[0], NicId=self.nic_id6).response.LinkNicId
        assert self.nic_link_id.startswith('eni-attach-')
        try:
            self.a1_r1.oapi.LinkNic(DeviceNumber=2, VmId=vm_ids[1], NicId=self.nic_id6)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9029')

    def test_T2647_empty_param(self):
        try:
            self.a1_r1.oapi.LinkNic()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2648_empty_nic_id(self):
        try:
            vm_ids = [self.inst_info[INSTANCE_ID_LIST][0]]
            wait_instances_state(self.a1_r1, vm_ids, state='running')
            self.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId=vm_ids[0], NicId='')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2649_invalid_nic_id(self):
        try:
            vm_ids = [self.inst_info[INSTANCE_ID_LIST][1]]
            wait_instances_state(self.a1_r1, vm_ids, state='running')
            self.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId=vm_ids[0], NicId='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2650_unknown_nic_id(self):
        try:
            vm_ids = [self.inst_info[INSTANCE_ID_LIST][2]]
            wait_instances_state(self.a1_r1, vm_ids, state='running')
            self.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId=vm_ids[0], NicId='eni-123154678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')

    def test_T2651_empty_vm_id(self):
        try:
            self.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId='', NicId=self.nic_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2652_invalid_vm_id(self):
        try:
            self.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId='toto', NicId=self.nic_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2653_unknown_vm_id(self):
        try:
            self.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId='i-123456789', NicId=self.nic_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')

    def test_T2654_missing_device_number(self):
        try:
            self.a1_r1.oapi.LinkNic(VmId='i-123456789', NicId=self.nic_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2655_missing_vm_id(self):
        try:
            self.a1_r1.oapi.LinkNic(DeviceNumber=1, NicId=self.nic_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2656_missing_nic(self):
        try:
            vm_ids = [self.inst_info[INSTANCE_ID_LIST][3]]
            wait_instances_state(self.a1_r1, vm_ids, state='running')
            self.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId=vm_ids[0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2657_vm_nic_not_in_same_subnet(self):
        try:
            vm_ids = [self.inst_info[INSTANCE_ID_LIST][4]]
            wait_instances_state(self.a1_r1, vm_ids, state='running')
            self.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId=vm_ids[0], NicId=self.nic_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T3482_dry_run(self):
        vm_ids = [self.vpc_inst_info[INSTANCE_ID_LIST][5]]
        wait_instances_state(self.a1_r1, vm_ids, state='running')
        ret = self.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId=vm_ids[0], NicId=self.nic_id, DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3483_other_account(self):
        vm_ids = [self.inst_info[INSTANCE_ID_LIST][5]]
        wait_instances_state(self.a1_r1, vm_ids, state='running')
        try:
            self.nic_link_id = self.a2_r1.oapi.LinkNic(DeviceNumber=1, VmId=vm_ids[0], NicId=self.nic_id).response.LinkNicId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5036')
