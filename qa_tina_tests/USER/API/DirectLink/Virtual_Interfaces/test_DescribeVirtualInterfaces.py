# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

import pytest
from qa_common_tools.test_base import OscTestSuite
import time


@pytest.mark.region_admin
class Test_DescribeVirtualInterfaces(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        cls.ret_loc = None
        cls.ret_alloc = None
        super(Test_DescribeVirtualInterfaces, cls).setup_class()
        try:
            cls.ret_loc = cls.a1_r1.directlink.DescribeLocations()
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret_alloc:
                cls.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=cls.ret_alloc.response.result.virtualInterfaceId)
        finally:
            super(Test_DescribeVirtualInterfaces, cls).teardown_class()

    @pytest.mark.region_directlink
    def test_T1913_without_param(self):
        ret = self.a1_r1.directlink.DescribeVirtualInterfaces()
        assert isinstance(ret.response.virtualInterfaces, list)
        assert not ret.response.virtualInterfaces

    @pytest.mark.region_admin
    @pytest.mark.region_directlink
    def test_T2994_describe_virtual_interfaces(self):
        retloc = None
        retcon1 = None
        vgw_id = None
        allocvitualinter = None
        try:
            retloc = self.a1_r1.directlink.DescribeLocations()
            ret = self.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1')
            vgw_id = ret.response.vpnGateway.vpnGatewayId
            retcon1 = self.a1_r1.directlink.CreateConnection(bandwidth='1Gbps', connectionName='test',
                                                             location=retloc.response.locations[0].locationCode)
            ret = self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=retcon1.response.connectionId)
            allocvitualinter = self.a1_r1.directlink.AllocatePrivateVirtualInterface(
                ownerAccount=self.a1_r1.config.account.account_id, connectionId=retcon1.response.connectionId,
                newPrivateVirtualInterfaceAllocation={'asn': 1, 'virtualGatewayId': vgw_id, 'virtualInterfaceName': 'test', 'vlan': 2})
            # hack because in2 does not have a real direct link
            if self.a1_r1.config.region.name != 'in-west-2':
                self.a1_r1.directlink.ConfirmPrivateVirtualInterface(virtualGatewayId=vgw_id,
                                                                     virtualInterfaceId=allocvitualinter.response.virtualInterfaceId)
            ret = self.a1_r1.directlink.DescribeVirtualInterfaces(virtualInterfaceId=allocvitualinter.response.virtualInterfaceId)
            # hack because in2 does not have a real direct link
            if self.a1_r1.config.region.name != 'in-west-2':
                assert ret.response.virtualInterfaces[0].virtualInterfaceState == 'pending'
            else:
                assert ret.response.virtualInterfaces[0].virtualInterfaceState == 'confirming'
            assert ret.response.virtualInterfaces[0].asn == 1
            assert ret.response.virtualInterfaces[0].vlan == 2
            assert ret.response.virtualInterfaces[0].ownerAccount == self.a1_r1.config.account.account_id
            assert ret.response.virtualInterfaces[0].connectionId == retcon1.response.connectionId
            assert ret.response.virtualInterfaces[0].connectionId.startswith('dxcon-')
            if self.a1_r1.config.region.name != 'in-west-2':
                assert ret.response.virtualInterfaces[0].virtualGatewayId == vgw_id
            assert ret.response.virtualInterfaces[0].virtualInterfaceId == allocvitualinter.response.virtualInterfaceId
            assert ret.response.virtualInterfaces[0].virtualInterfaceType == 'private'
            assert ret.response.virtualInterfaces[0].virtualInterfaceName == 'test'
            assert len(ret.response.virtualInterfaces) == 1
        finally:
            if allocvitualinter:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=allocvitualinter.response.virtualInterfaceId)
            if retcon1:
                self.a1_r1.intel.dl.connection.delete(owner=self.a1_r1.config.account.account_id, connection_id=retcon1.response.connectionId)
            if vgw_id:
                self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=vgw_id)
