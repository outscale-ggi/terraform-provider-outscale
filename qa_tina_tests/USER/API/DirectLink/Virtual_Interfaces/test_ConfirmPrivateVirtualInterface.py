# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

import pytest
import time

from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina import wait_tools


@pytest.mark.region_admin
class Test_ConfirmPrivateVirtualInterface(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.conn_id = None
        cls.vgw_id = None
        cls.QUOTAS = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        super(Test_ConfirmPrivateVirtualInterface, cls).setup_class()
        ret = cls.a1_r1.directlink.DescribeLocations()
        ret = cls.a1_r1.directlink.CreateConnection(location=ret.response.locations[0].locationCode, bandwidth='1Gbps',
                                                    connectionName=id_generator(prefix='dl_'))
        cls.conn_id = ret.response.connectionId

    @classmethod
    def teardown_class(cls):
        try:
            if cls.conn_id:
                cls.a1_r1.intel.dl.connection.delete(owner=cls.a1_r1.config.account.account_id, connection_id=cls.conn_id)
        finally:
            super(Test_ConfirmPrivateVirtualInterface, cls).teardown_class()

    @pytest.mark.region_admin
    @pytest.mark.region_directlink
    def test_T1915_required_param(self):
        newPrivateVirtualInterfaceAllocation = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        alloc_info = None
        try:
            ret = self.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1')
            self.vgw_id = ret.response.vpnGateway.vpnGatewayId
            wait_tools.wait_vpn_gateways_state(self.a1_r1, [self.vgw_id], state='available')
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            alloc_info = self.a1_r1.directlink.AllocatePrivateVirtualInterface(
                connectionId=self.conn_id, newPrivateVirtualInterfaceAllocation=newPrivateVirtualInterfaceAllocation,
                ownerAccount=self.a1_r1.config.account.account_id)
            ret = self.a1_r1.directlink.ConfirmPrivateVirtualInterface(virtualGatewayId=self.vgw_id,
                                                                       virtualInterfaceId=alloc_info.response.virtualInterfaceId)
            assert ret.response.virtualInterfaceState == 'pending'
        finally:
            if alloc_info:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=alloc_info.response.virtualInterfaceId)
                for _ in range(18):
                    resp = self.a1_r1.directlink.DescribeVirtualInterfaces(virtualInterfaceId=alloc_info.response.virtualInterfaceId).response
                    assert len(resp.virtualInterfaces) == 1
                    if resp.virtualInterfaces[0].virtualInterfaceState == 'deleted':
                        break
                    time.sleep(10)
            if self.vgw_id:
                self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=self.vgw_id)
                wait_tools.wait_vpn_gateways_state(self.a1_r1, [self.vgw_id], state='deleted')
