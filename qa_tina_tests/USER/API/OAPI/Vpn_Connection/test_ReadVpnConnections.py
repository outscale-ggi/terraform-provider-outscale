# -*- coding:utf-8 -*-
# -*- coding:utf-8 -*-

from qa_tina_tests.USER.API.OAPI.Vpn_Connection.VpnConnection import VpnConnection, validate_vpn_connection
from qa_test_tools.test_base import known_error
from qa_sdk_common.exceptions.osc_exceptions import OscApiException


class Test_ReadVpnConnections(VpnConnection):

    @classmethod
    def setup_class(cls):
        super(Test_ReadVpnConnections, cls).setup_class()
        try:
            cls.a1_r1.oapi.CreateVpnConnectionRoute(VpnConnectionId=cls.vpn_id, DestinationIpRange='172.13.1.4/24')
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        super(Test_ReadVpnConnections, cls).teardown_class()

    def test_T3363_empty_filters(self):
        ret = self.a1_r1.oapi.ReadVpnConnections()
        assert len(ret.response.VpnConnections) == 2
        VpnConnections1 = ret.response.VpnConnections[0]
        assert VpnConnections1.ClientGatewayId
        assert VpnConnections1.ConnectionType
        assert VpnConnections1.Routes
        assert VpnConnections1.State
        assert VpnConnections1.StaticRoutesOnly
        assert hasattr(VpnConnections1, "Tags")
        assert VpnConnections1.VirtualGatewayId
        assert VpnConnections1.VpnConnectionId
        try:
            assert not hasattr(VpnConnections1, 'ClientGatewayConfiguration')
            known_error('GTW-1081', 'ClientGatewayConfiguration is not in the response')
        except OscApiException:
            assert False, 'Remove known error'

        
    def test_T3364_filters_bgp_asns(self):
        assert len(self.a1_r1.oapi.ReadVpnConnections(Filters={'BgpAsns': [self.bgp_asn]}).response.VpnConnections) == 1

    def test_T3365_filters_client_gateway_ids_id1(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'ClientGatewayIds': [self.cg_id]}).response.VpnConnections
        for vpn in ret:
            validate_vpn_connection(vpn, expected_vpn={'ClientGatewayId': self.cg_id})

    def test_T3366_filters_client_gateway_ids_id2(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'ClientGatewayIds': [self.cg_id2]}).response.VpnConnections
        for vpn in ret:
            validate_vpn_connection(vpn, expected_vpn={'ClientGatewayId': self.cg_id2})

    def test_T3367_filters_vpn_connection_ids_id1(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'VpnConnectionIds': [self.vpn_id]}).response.VpnConnections
        for vpn in ret:
            validate_vpn_connection(vpn, expected_vpn={'VpnConnectionId': self.vpn_id})

    def test_T3368_filters_vpn_connection_ids_id2(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'VpnConnectionIds': [self.vpn_id2]}).response.VpnConnections
        for vpn in ret:
            validate_vpn_connection(vpn, expected_vpn={'VpnConnectionId': self.vpn_id2})

    def test_T3369_filters_states_pending(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'States': ['pending']}).response.VpnConnections
        assert len(ret) > 0
        for vpn in ret:
            validate_vpn_connection(vpn, expected_vpn={'State': 'pending'})

    def test_T3370_filters_states_deleted(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'States': ['deleted']}).response.VpnConnections
        for vpn in ret:
            validate_vpn_connection(vpn, expected_vpn={'State': 'deleted'})

    def test_T3371_filters_static_routes_only_true(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'StaticRoutesOnly': True}).response.VpnConnections
        for vpn in ret:
            validate_vpn_connection(vpn, expected_vpn={'StaticRoutesOnly': True})

    def test_T3372_filters_static_routes_only_false(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'StaticRoutesOnly': False}).response.VpnConnections
        for vpn in ret:
            validate_vpn_connection(vpn, expected_vpn={'StaticRoutesOnly': False})

    def test_T3373_filters_connection_types_invalid(self):
        assert len(self.a1_r1.oapi.ReadVpnConnections(Filters={'ConnectionTypes': ['tata']}).response.VpnConnections) == 0

    def test_T3374_filters_connection_types_ipsec1(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'ConnectionTypes': ['ipsec.1']}).response.VpnConnections
        assert len(ret) > 0
        for vpn in ret:
            validate_vpn_connection(vpn, expected_vpn={'ConnectionType': 'ipsec.1'})

    def test_T3580_filters_route_destination_ip_ranges(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'RouteDestinationIpRanges': ['172.13.1.4/24']}).response.VpnConnections
        assert len(ret) > 0
        for vpn in ret:
            validate_vpn_connection(vpn, routes=[{'DestinationIpRange': '172.13.1.4/24', 'State': 'available'}])

    def test_T3581_filters_virtual_gateway_ids_id1(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'VirtualGatewayIds': [self.vg_id]}).response.VpnConnections
        for vpn in ret:
            validate_vpn_connection(vpn, expected_vpn={'VirtualGatewayId': self.vg_id})

    def test_T3582_filters_virtual_gateway_ids_id2(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'VirtualGatewayIds': [self.vg_id2]}).response.VpnConnections
        for vpn in ret:
            validate_vpn_connection(vpn, expected_vpn={'VirtualGatewayId': self.vg_id2})
