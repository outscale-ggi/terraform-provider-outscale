# -*- coding:utf-8 -*-
import pytest

from qa_tina_tests.USER.API.OAPI.Nic.Nic import Nic
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.specs.check_tools import check_oapi_response
from qa_tina_tools.tools.tina.wait_tools import wait_network_interfaces_state
from qa_sdk_common.exceptions.osc_exceptions import OscApiException


class Test_ReadNics(Nic):

    @classmethod
    def setup_class(cls):
        super(Test_ReadNics, cls).setup_class()
        cls.nic_id = None
        cls.nic_id2 = None
        cls.nic_id3 = None
        cls.vm_info = None
        cls.vm_ids = None
        cls.nic_link_id = None
        try:
            ret = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic
            cls.nic_id = ret.NicId
            cls.a1_r1.oapi.LinkPrivateIps(NicId=cls.nic_id, PrivateIps=['10.0.1.35', '10.0.1.36', '10.0.1.37', '10.0.1.38'])
            ret = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic
            cls.nic_id2 = ret.NicId
            cls.a1_r1.oapi.LinkPrivateIps(NicId=cls.nic_id2, PrivateIps=['10.0.1.135'])
            ret = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id2).response.Nic
            cls.nic_id3 = ret.NicId
            cls.vm_info = create_instances(cls.a1_r1, subnet_id=cls.subnet_id1, sg_id_list=[cls.firewall_id1], state='running', inst_type='c4.large')
            cls.vm_ids = cls.vm_info[INSTANCE_ID_LIST]
            cls.nic_link_id = cls.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId=cls.vm_ids[0], NicId=cls.nic_id).response.LinkNicId
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.nic_id3:
                cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id3)
            if cls.nic_id2:
                cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id2)
            if cls.nic_id:
                cls.a1_r1.fcu.DetachNetworkInterface(AttachmentId=cls.nic_link_id)
                wait_network_interfaces_state(osc_sdk=cls.a1_r1, network_interface_id_list=[cls.nic_id], state='available')
                cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id)
            if cls.vm_info:
                delete_instances(cls.a1_r1, cls.vm_info)
        except OscApiException as err:
            raise err
        finally:
            super(Test_ReadNics, cls).teardown_class()

    def test_T2679_empty_filters(self):
        resp = self.a1_r1.oapi.ReadNics().response
        check_oapi_response(resp, 'ReadNicsResponse')
#         assert len(ret) == 4
#         nic = next((x for x in ret if x.NicId == self.nic_id), None)
#         assert nic.AccountId == self.a1_r1.config.account.account_id
#         assert nic.Description == ''
#         assert nic.IsSourceDestChecked is not None
#
#         assert nic.NicId.startswith('eni-')
#
#         assert len(nic.SecurityGroups) == 1
#         assert nic.SecurityGroups[0].SecurityGroupId is not None
#         assert nic.SecurityGroups[0].SecurityGroupName is not None
#         assert nic.MacAddress != ''
#         assert nic.NetId == self.vpc_id1
#         assert nic.NicId.startswith('eni-'), "Invalid prefix: The nic ID must begin with 'eni-'"
#         assert nic.NicLink is not None
#         assert nic.PrivateDnsName is not None
#         assert len(nic.PrivateIps) == 5
#         for ip in nic.PrivateIps:
#             if ip.IsPrimary:
#                 assert ip.PrivateIp is not None
#                 assert ip.PrivateDnsName is not None
#                 assert ip.LinkPublicIp is not None
#             else:
#                 assert ip.PrivateIp in ['10.0.1.35', '10.0.1.36', '10.0.1.37', '10.0.1.38']
#                 assert ip.PrivateDnsName is not None
#                 assert ip.LinkPublicIp is not None
#         assert nic.LinkPublicIp is not None
#         assert nic.State == 'available'
#         assert nic.SubnetId == self.subnet_id1
#         assert nic.SubregionName == self.a1_r1.config.region.az_name
#         assert nic.Tags == []

    def test_T2680_filters_nic_id1(self):
        resp = self.a1_r1.oapi.ReadNics(Filters={'NicIds': [self.nic_id]}).response
        check_oapi_response(resp, 'ReadNicsResponse')
#         assert len(ret) == 1
#         nic = ret[0]
#         assert nic.NicId.startswith('eni-')
#         assert nic.AccountId == self.a1_r1.config.account.account_id
#         assert nic.Description == ''
#         assert len(nic.SecurityGroups) == 1
#         assert nic.SecurityGroups[0].SecurityGroupId is not None
#         assert nic.SecurityGroups[0].SecurityGroupName is not None
#         assert not nic.IsSourceDestChecked
#         assert nic.MacAddress != ''
#         assert nic.NetId == self.vpc_id1
#         assert nic.NicId.startswith('eni-'), "Invalid prefix: The nic ID must begin with 'eni-'"
#         assert nic.NicLink is not None
#         assert nic.PrivateDnsName is not None
#         assert len(nic.PrivateIps) == 5
#         for ip in nic.PrivateIps:
#             if ip.IsPrimary:
#                 assert ip.PrivateIp is not None
#                 assert ip.PrivateDnsName is not None
#                 assert ip.LinkPublicIp is not None
#             else:
#                 assert ip.PrivateIp in ['10.0.1.35', '10.0.1.36', '10.0.1.37', '10.0.1.38']
#                 assert ip.PrivateDnsName is not None
#                 assert ip.LinkPublicIp is not None
#         assert nic.LinkPublicIp is not None
#         assert nic.State == 'available'
#         assert nic.SubnetId == self.subnet_id1
#         assert nic.SubregionName == self.a1_r1.config.region.az_name
#         assert nic.Tags == []

    def test_T2681_filters_nic_ids_1_and_2(self):
        ret = self.a1_r1.oapi.ReadNics(Filters={'NicIds': [self.nic_id, self.nic_id2]}).response.Nics
        assert len(ret) == 2

    def test_T2684_filters_subnet_id(self):
        ret = self.a1_r1.oapi.ReadNics(Filters={'SubnetIds': [self.subnet_id2]}).response.Nics
        assert len(ret) == 1
        nic = ret[0]
        assert nic.NicId == self.nic_id3
        assert nic.SubnetId == self.subnet_id2

    def test_T2685_filters_private_ip(self):
        ret = self.a1_r1.oapi.ReadNics(Filters={'PrivateIpsPrivateIps': ['10.0.1.38']}).response.Nics
        assert len(ret) == 1
        nic = ret[0]
        assert nic.NicId == self.nic_id

    def test_T2686_filters_vm_ids(self):
        ret = self.a1_r1.oapi.ReadNics(Filters={'LinkNicVmIds': [self.vm_ids[0]]}).response.Nics
        assert len(ret) == 2  # The 'attached/ing' and the 'detaching/ed'
        for nic in ret:
            link = nic.LinkNic
            if link.State in ['attached', 'attaching'] and nic.Description == "":
                assert link.LinkNicId == self.nic_link_id
                assert link.DeviceNumber == 1
            if link.State == ('detaching' or 'detached')and nic.Description == "":
                assert nic.NicId != self.nic_id
                assert link.LinkNicId != self.nic_link_id
            assert link.VmId == self.vm_ids[0]

    @pytest.mark.tag_sec_confidentiality
    def test_T3403_with_other_account(self):
        ret = self.a2_r1.oapi.ReadNics()
        assert not ret.response.Nics

    @pytest.mark.tag_sec_confidentiality
    def test_T3410_with_other_account_inexistante_nic(self):
        ret = self.a2_r1.oapi.ReadNics(Filters={'NicIds': [self.nic_id, self.nic_id2]}).response.Nics
        assert not ret
