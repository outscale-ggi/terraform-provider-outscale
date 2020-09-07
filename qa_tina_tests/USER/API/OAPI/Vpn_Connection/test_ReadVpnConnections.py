# -*- coding:utf-8 -*-
# -*- coding:utf-8 -*-
from qa_test_tools.misc import assert_oapi_error
from qa_tina_tests.USER.API.OAPI.Vpn_Connection.VpnConnection import \
    VpnConnection, validate_vpn_connection
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.specs.check_tools import check_oapi_response
from qa_tina_tools.tools.tina.wait_tools import wait_vpn_connections_state, wait_vpn_gateways_state, \
    wait_customer_gateways_state

NUM_VPN_CONN = 1


class Test_ReadVpnConnections(VpnConnection):

    @classmethod
    def setup_class(cls):
        super(Test_ReadVpnConnections, cls).setup_class()
        cls.vpn_ids = []
        cls.cgw_ids = []
        cls.vgw_ids = []
        try:
            cls.a1_r1.oapi.CreateVpnConnectionRoute(VpnConnectionId=cls.vpn_id, DestinationIpRange='172.13.1.4/24')

            for i in range(NUM_VPN_CONN):
                # Virtual Gateway
                cls.vgw_ids.append(cls.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1')
                                   .response.VirtualGateway.VirtualGatewayId)

                cls.cgw_ids.append(cls.a1_r1.oapi.CreateClientGateway(
                    BgpAsn=cls.bgp_asn + 2 + i, PublicIp=cls.cgw_ip,
                    ConnectionType='ipsec.1').response.ClientGateway.ClientGatewayId)

                cls.vpn_ids.append(cls.a1_r1.oapi.CreateVpnConnection(
                    ClientGatewayId=cls.cgw_ids[-1], VirtualGatewayId=cls.vgw_ids[-1], ConnectionType='ipsec.1',
                    StaticRoutesOnly=False).response.VpnConnection.VpnConnectionId)

            cls.a1_r1.oapi.CreateTags(ResourceIds=cls.vpn_ids[0:1], Tags=[{'Key': 'vpn_key', 'Value': 'vpn_value'}])
            if NUM_VPN_CONN > 1:
                cls.a1_r1.oapi.CreateTags(ResourceIds=cls.vpn_ids[1:2], Tags=[{'Key': 'vpn_key1', 'Value': 'vpn_value'}])
            if NUM_VPN_CONN > 2:
                cls.a1_r1.oapi.CreateTags(ResourceIds=cls.vpn_ids[2:3], Tags=[{'Key': 'vpn_key', 'Value': 'vpn_value1'}])

        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpn_ids:
                for vpn_id in cls.vpn_ids:
                    cls.a1_r1.oapi.DeleteVpnConnection(VpnConnectionId=vpn_id)
                    wait_vpn_connections_state(cls.a1_r1, [vpn_id], state='deleted', wait_time=5, threshold=60)
            if cls.cgw_ids:
                for cgw_id in cls.cgw_ids:
                    cls.a1_r1.oapi.DeleteClientGateway(ClientGatewayId=cgw_id)
                    wait_customer_gateways_state(cls.a1_r1, [cgw_id], state='deleted')
            if cls.vgw_ids:
                for vgw_id in cls.vgw_ids:
                    cls.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id)
                    wait_vpn_gateways_state(cls.a1_r1, [vgw_id], state='deleted')

                # wait_vpn_connections_state(cls.a1_r1, cls.vpn_ids, state='deleted', wait_time=5, threshold=60)
        finally:
            super(Test_ReadVpnConnections, cls).teardown_class()

    def test_T3363_empty_filters(self):
        ret = self.a1_r1.oapi.ReadVpnConnections()
        assert len(ret.response.VpnConnections) == 2 + NUM_VPN_CONN
        check_oapi_response(ret.response, "ReadVpnConnectionsResponse")

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
        assert len(
            self.a1_r1.oapi.ReadVpnConnections(Filters={'ConnectionTypes': ['tata']}).response.VpnConnections) == 0

    def test_T3374_filters_connection_types_ipsec1(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'ConnectionTypes': ['ipsec.1']}).response.VpnConnections
        assert len(ret) > 0
        for vpn in ret:
            validate_vpn_connection(vpn, expected_vpn={'ConnectionType': 'ipsec.1'})

    def test_T3580_filters_route_destination_ip_ranges(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(
            Filters={'RouteDestinationIpRanges': ['172.13.1.4/24']}).response.VpnConnections
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

    def test_T5115_filters_tags(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={"Tags": ['vpn_key=vpn_value']}).response.VpnConnections
        assert len(ret) == 1

    def test_T5116_filters_tagkeys(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={"TagKeys": ['vpn_key']}).response.VpnConnections
        assert len(ret) == 2

    def test_T5117_filters_tagvalues(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={"TagValues": ['vpn_value']}).response.VpnConnections
        assert len(ret) == 2

    def test_T5118_filters_invalid_tags(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(
            Filters={"Tags": ['incorrect_vpn=incorrect_vpn_value']}).response.VpnConnections
        assert len(ret) == 0

    def test_T5119_filters_incorrect_tags_type(self):
        try:
            self.a1_r1.oapi.ReadVpnConnections(
                Filters={"Tags": 'vpn=vpn_value'}).response.VpnConnections
            assert False, 'Call should fail'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')