# -*- coding:utf-8 -*-
import pytest

from qa_tina_tests.USER.API.OAPI.Nic.Nic import Nic
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_network_interfaces_state

NUM_NIC = 3


class Test_UnlinkNic(Nic):

    @classmethod
    def setup_class(cls):
        super(Test_UnlinkNic, cls).setup_class()
        cls.nic_ids = []
        cls.vm_info = None
        cls.vm_ids = None
        try:
            for _ in range(NUM_NIC):
                cls.nic_ids.append(cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic.NicId)
            wait_network_interfaces_state(osc_sdk=cls.a1_r1, network_interface_id_list=cls.nic_ids, state='available')
            cls.vm_info = create_instances(cls.a1_r1, nb=3, subnet_id=cls.subnet_id1, sg_id_list=[cls.firewall_id1], state='ready')
            cls.vm_ids = cls.vm_info[INSTANCE_ID_LIST]
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vm_info:
                delete_instances(cls.a1_r1, cls.vm_info)
            if cls.nic_ids:
                wait_network_interfaces_state(osc_sdk=cls.a1_r1, network_interface_id_list=cls.nic_ids, state='available')
                for nic_id in cls.nic_ids:
                    cls.a1_r1.oapi.DeleteNic(NicId=nic_id)
        finally:
            super(Test_UnlinkNic, cls).teardown_class()

    def test_T2687_empty_param(self):
        try:
            self.a1_r1.oapi.UnlinkNic()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2688_empty_nic_link_id(self):
        try:
            self.a1_r1.oapi.UnlinkNic(LinkNicId='')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2689_invalid_nic_link_id(self):
        try:
            self.a1_r1.oapi.UnlinkNic(LinkNicId='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2690_unknown_nic_link_id(self):
        try:
            self.a1_r1.oapi.UnlinkNic(LinkNicId='eni-attach-123154678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')

    def test_T2691_valid_case(self):
        nic_id = self.nic_ids[0]
        wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[nic_id], state='available')
        nic_link_id = self.a1_r1.fcu.AttachNetworkInterface(DeviceIndex='1', InstanceId=self.vm_ids[0],
                                                            NetworkInterfaceId=nic_id).response.attachmentId
        wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[nic_id], state='in-use')
        self.a1_r1.oapi.UnlinkNic(LinkNicId=nic_link_id)

    def test_T3492_dry_run(self):
        nic_link_id = None
        try:
            nic_id = self.nic_ids[1]
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[nic_id], state='available')
            nic_link_id = self.a1_r1.fcu.AttachNetworkInterface(DeviceIndex='1', InstanceId=self.vm_ids[1],
                                                                NetworkInterfaceId=nic_id).response.attachmentId
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[nic_id], state='in-use')
            ret = self.a1_r1.oapi.UnlinkNic(LinkNicId=nic_link_id, DryRun=True)
            assert_dry_run(ret)
        finally:
            if nic_link_id:
                self.a1_r1.oapi.UnlinkNic(LinkNicId=nic_link_id)

    @pytest.mark.tag_sec_confidentiality
    def test_T3493_other_account(self):
        nic_id = self.nic_ids[2]
        wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[nic_id], state='available')
        nic_link_id = self.a1_r1.fcu.AttachNetworkInterface(DeviceIndex='1', InstanceId=self.vm_ids[2],
                                                            NetworkInterfaceId=nic_id).response.attachmentId
        wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[nic_id], state='in-use')
        try:
            self.a2_r1.oapi.UnlinkNic(LinkNicId=nic_link_id,)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5007')
        finally:
            self.a1_r1.oapi.UnlinkNic(LinkNicId=nic_link_id)
