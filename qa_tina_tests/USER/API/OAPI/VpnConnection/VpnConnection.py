

from qa_test_tools.config.configuration import Configuration
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import wait
from qa_tina_tools.tools.tina.wait_tools import wait_vpn_gateways_state, wait_customer_gateways_state


def validate_vpn_connection(vpn, **kwargs):
    expected_vpn = kwargs.get('expected_vpn')
    routes = kwargs.get('routes')
    if expected_vpn:
        for key, value in expected_vpn.items():
            assert getattr(vpn, key) == value, (
                'In VpnConnection, {} is different of expected value {} for key {}'
                .format(getattr(vpn, key), value, key))
    if routes:
        for route in vpn.Routes:
            for exp_route in routes:
                if exp_route.get('DestinationIpRange') == route.DestinationIpRange:
                    for key, value in exp_route.items():
                        assert getattr(route, key) == value, (
                            'In VpnConnection, {} is different of expected value {} for key {}'
                            .format(getattr(route, key), value, key))
    assert vpn.VpnConnectionId.startswith('vpn-')


class VpnConnection(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.vg_id = None
        cls.cg_id = None
        cls.vpn_id = None
        cls.vg_id2 = None
        cls.cg_id2 = None
        cls.vpn_id2 = None
        super(VpnConnection, cls).setup_class()
        try:
            # Virtual Gateway
            cls.vg_id = cls.a1_r1.oapi.CreateVirtualGateway(
                ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
            cls.vg_id2 = cls.a1_r1.oapi.CreateVirtualGateway(
                ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
            # Client Gateway
            cls.cgw_ip = Configuration.get('ipaddress', 'cgw_ip')
            cls.bgp_asn = 6025573
            cls.cg_id = cls.a1_r1.oapi.CreateClientGateway(
                BgpAsn=cls.bgp_asn, PublicIp=cls.cgw_ip, ConnectionType='ipsec.1').response.ClientGateway.ClientGatewayId
            cls.cg_id2 = cls.a1_r1.oapi.CreateClientGateway(
                BgpAsn=cls.bgp_asn + 1, PublicIp=cls.cgw_ip, ConnectionType='ipsec.1').response.ClientGateway.ClientGatewayId
            # Vpn Connection
            cls.vpn_id = cls.a1_r1.oapi.CreateVpnConnection(
                ClientGatewayId=cls.cg_id, VirtualGatewayId=cls.vg_id, ConnectionType='ipsec.1',
                StaticRoutesOnly=True).response.VpnConnection.VpnConnectionId
            cls.a1_r1.oapi.CreateVpnConnectionRoute(VpnConnectionId=cls.vpn_id, DestinationIpRange='172.13.1.4/24')
            cls.vpn_id2 = cls.a1_r1.oapi.CreateVpnConnection(
                ClientGatewayId=cls.cg_id2, VirtualGatewayId=cls.vg_id2, ConnectionType='ipsec.1',
                StaticRoutesOnly=False).response.VpnConnection.VpnConnectionId
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        error = []
        try:
            if cls.vpn_id:
                cls.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=cls.vpn_id)
                wait.wait_VpnConnections_state(cls.a1_r1, [cls.vpn_id], cleanup=True, state='deleted', wait_time=5, threshold=60)
        except Exception as err:
            error.append(err)
        try:
            if cls.vpn_id2:
                cls.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=cls.vpn_id2)
                wait.wait_VpnConnections_state(cls.a1_r1, [cls.vpn_id2], cleanup=True, state='deleted', wait_time=5, threshold=60)
        except Exception as err:
            error.append(err)
        try:
            if cls.vg_id:
                cls.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=cls.vg_id)
                wait_vpn_gateways_state(cls.a1_r1, [cls.vg_id], state='deleted')
        except Exception as err:
            error.append(err)
        try:
            if cls.vg_id2:
                cls.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=cls.vg_id2)
                wait_vpn_gateways_state(cls.a1_r1, [cls.vg_id2], state='deleted')
        except Exception as err:
            error.append(err)
        try:
            if cls.cg_id:
                cls.a1_r1.fcu.DeleteCustomerGateway(CustomerGatewayId=cls.cg_id)
                wait_customer_gateways_state(cls.a1_r1, [cls.cg_id], state='deleted')
        except Exception as err:
            error.append(err)
        try:
            if cls.cg_id2:
                cls.a1_r1.fcu.DeleteCustomerGateway(CustomerGatewayId=cls.cg_id2)
                wait_customer_gateways_state(cls.a1_r1, [cls.cg_id2], state='deleted')
        except Exception as err:
            error.append(err)
        finally:
            super(VpnConnection, cls).teardown_class()
            if error:
                raise error[0]
