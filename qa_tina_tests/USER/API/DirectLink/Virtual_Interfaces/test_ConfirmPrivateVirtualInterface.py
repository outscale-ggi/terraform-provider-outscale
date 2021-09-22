
import time

import pytest

from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina import wait_tools


@pytest.mark.region_admin
@pytest.mark.region_directlink
class Test_ConfirmPrivateVirtualInterface(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.conn_id = None
        cls.quotas = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        cls.known_error = False
        super(Test_ConfirmPrivateVirtualInterface, cls).setup_class()
        try:
            ret = cls.a1_r1.directlink.DescribeLocations()
            if cls.a1_r1.config.region.name == 'in-west-2':
                if len(ret.response.locations) == 0:
                    cls.known_error = True
                    return
                assert False, 'remove known error'
            cls.location_code = ret.response.locations[0].locationCode
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    def setup_method(self, method):
        self.conn_id = None
        if self.known_error:
            return
        OscTinaTest.setup_method(self, method)
        ret = self.a1_r1.directlink.CreateConnection(location=self.location_code, bandwidth='1Gbps', connectionName=id_generator(prefix='dl_'))
        self.conn_id = ret.response.connectionId

    def teardown_method(self, method):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        try:
            if self.conn_id:
                self.a1_r1.intel.dl.connection.delete(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
        finally:
            OscTinaTest.teardown_method(self, method)

    def test_T1915_required_param(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        allocation = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        alloc_info = None
        vgw_id = None
        try:
            vgw_id = self.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1').response.vpnGateway.vpnGatewayId
            wait_tools.wait_vpn_gateways_state(self.a1_r1, [vgw_id], state='available')
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            alloc_info = self.a1_r1.directlink.AllocatePrivateVirtualInterface(
                connectionId=self.conn_id, newPrivateVirtualInterfaceAllocation=allocation,
                ownerAccount=self.a1_r1.config.account.account_id)
            ret = self.a1_r1.directlink.ConfirmPrivateVirtualInterface(virtualGatewayId=vgw_id,
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
            if vgw_id:
                self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=vgw_id)
                wait_tools.wait_vpn_gateways_state(self.a1_r1, [vgw_id], state='deleted')

    def test_T5738_with_extra_param(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        allocation = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        alloc_info = None
        vgw_id = None
        try:
            vgw_id = self.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1').response.vpnGateway.vpnGatewayId
            wait_tools.wait_vpn_gateways_state(self.a1_r1, [vgw_id], state='available')
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            alloc_info = self.a1_r1.directlink.AllocatePrivateVirtualInterface(
                connectionId=self.conn_id, newPrivateVirtualInterfaceAllocation=allocation,
                ownerAccount=self.a1_r1.config.account.account_id)
            ret = self.a1_r1.directlink.ConfirmPrivateVirtualInterface(virtualGatewayId=vgw_id,
                                                                       virtualInterfaceId=alloc_info.response.virtualInterfaceId,
                                                                       Foo='Bar')
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
            if vgw_id:
                self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=vgw_id)
                wait_tools.wait_vpn_gateways_state(self.a1_r1, [vgw_id], state='deleted')
