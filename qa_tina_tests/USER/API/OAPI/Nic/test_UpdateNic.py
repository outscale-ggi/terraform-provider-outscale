# -*- coding:utf-8 -*-
import pytest

from qa_tina_tests.USER.API.OAPI.Nic.Nic import Nic
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST


class Test_UpdateNic(Nic):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateNic, cls).setup_class()
        cls.nic_id = None
        cls.vm_info = None
        cls.vm_ids = None
        cls.nic_link_id = None
        try:
            ret = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic
            cls.nic_id = ret.NicId
            cls.vm_info = create_instances(cls.a1_r1, subnet_id=cls.subnet_id1, sg_id_list=[cls.firewall_id1],
                                           state='running')
            cls.vm_ids = cls.vm_info[INSTANCE_ID_LIST]
            cls.nic_link_id = cls.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId=cls.vm_ids[0],
                                                     NicId=cls.nic_id).response.LinkNicId
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.nic_link_id:
                cls.a1_r1.oapi.UnlinkNic(LinkNicId=cls.nic_link_id)
            if cls.vm_info:
                delete_instances(cls.a1_r1, cls.vm_info)
            if cls.nic_id:
                cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id)
        finally:
            super(Test_UpdateNic, cls).teardown_class()

    def test_T2704_with_empty_param(self):
        try:
            self.a1_r1.oapi.UpdateNic()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2705_with_empty_nic_id(self):
        try:
            self.a1_r1.oapi.UpdateNic(NicId='')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2706_with_invalid_nic_id(self):
        try:
            self.a1_r1.oapi.UpdateNic(NicId='toto', Description='new_description')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2707_with_unknown_nic_id(self):
        try:
            self.a1_r1.oapi.UpdateNic(NicId='eni-12345678',
                                      Description='new_description')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5036')

    def test_T2708_with_valid_nic_id(self):
        try:
            self.a1_r1.oapi.UpdateNic(NicId=self.nic_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2709_with_description(self):
        self.a1_r1.oapi.UpdateNic(NicId=self.nic_id, Description='new_description')

    def test_T2710_with_empty_firewall_rules_set_ids(self):
        try:
            self.a1_r1.oapi.UpdateNic(NicId=self.nic_id, SecurityGroupIds=[])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2711_with_invalid_firewall_rules_set_ids(self):
        try:
            self.a1_r1.oapi.UpdateNic(NicId=self.nic_id, SecurityGroupIds=['tata', 'toto'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2712_with_unknown_firewall_rules_set_ids(self):
        try:
            self.a1_r1.oapi.UpdateNic(NicId=self.nic_id, SecurityGroupIds=['sg-123456789', 'sg-12478516'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')

    def test_T2713_with_valid_firewall_rules_set_ids(self):
        self.a1_r1.oapi.UpdateNic(NicId=self.nic_id, SecurityGroupIds=[self.firewall_id1])

    def test_T2714_with_double_param_update(self):
        self.a1_r1.oapi.UpdateNic(NicId=self.nic_id, Description='', SecurityGroupIds=[self.firewall_id1])

    def test_T3513_dry_run(self):
        ret = self.a1_r1.oapi.UpdateNic(NicId=self.nic_id, Description='new_description', DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3514_other_account(self):
        try:
            self.a2_r1.oapi.UpdateNic(NicId=self.nic_id, Description='new_description')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5036')
