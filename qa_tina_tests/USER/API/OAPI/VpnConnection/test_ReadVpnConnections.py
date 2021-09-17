

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.tools.tina import wait_tools
from qa_tina_tests.USER.API.OAPI.VpnConnection.VpnConnection import VpnConnection, validate_vpn_connection

NUM_VPN_CONN = 4

class Test_ReadVpnConnections(VpnConnection):

    @classmethod
    def setup_class(cls):
        cls.vpn_ids = []
        cls.cgw_ids = []
        cls.vgw_ids = []
        cls.quotas = {'vpg_limit': 6, 'vpnc_limit': 6, 'cgw_limit': 6}
        super(Test_ReadVpnConnections, cls).setup_class()
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

            cls.a1_r1.oapi.CreateTags(ResourceIds=cls.vpn_ids[0:1], Tags=[{'Key': 'toto', 'Value': 'titi'}])
            if NUM_VPN_CONN > 1:
                cls.a1_r1.oapi.CreateTags(ResourceIds=cls.vpn_ids[1:2], Tags=[{'Key': 'toto1', 'Value': 'titi'}])
            if NUM_VPN_CONN > 2:
                cls.a1_r1.oapi.CreateTags(ResourceIds=cls.vpn_ids[2:3], Tags=[{'Key': 'toto', 'Value': 'titi1'}])

        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpn_ids:
                for vpn_id in cls.vpn_ids:
                    cls.a1_r1.oapi.DeleteVpnConnection(VpnConnectionId=vpn_id)
                    wait_tools.wait_vpn_connections_state(cls.a1_r1, [vpn_id], state='deleted', wait_time=5, threshold=60)
            if cls.cgw_ids:
                for cgw_id in cls.cgw_ids:
                    cls.a1_r1.oapi.DeleteClientGateway(ClientGatewayId=cgw_id)
                    wait_tools.wait_customer_gateways_state(cls.a1_r1, [cgw_id], state='deleted')
            if cls.vgw_ids:
                for vgw_id in cls.vgw_ids:
                    cls.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id)
                    wait_tools.wait_vpn_gateways_state(cls.a1_r1, [vgw_id], state='deleted')

                # wait_vpn_connections_state(cls.a1_r1, cls.vpn_ids, state='deleted', wait_time=5, threshold=60)
        finally:
            super(Test_ReadVpnConnections, cls).teardown_class()

    def test_T3363_empty_filters(self):
        ret = self.a1_r1.oapi.ReadVpnConnections()
        assert len(ret.response.VpnConnections) == 2 + NUM_VPN_CONN
        ret.check_response()

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

    def test_T5137_filters_route_destination_ip_ranges_invalid_type(self):
        try:
            self.a1_r1.oapi.ReadVpnConnections(Filters={'RouteDestinationIpRanges': False})
            assert False, 'Call should fail'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5138_filters_route_destination_ip_ranges_invalid_value(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'RouteDestinationIpRanges': ['foo']})
        assert len(ret.response.VpnConnections) == 0

    def test_T5139_filters_route_destination_ip_ranges_invalid_range(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'RouteDestinationIpRanges': ['10.0.0.0/'], 'VpnConnectionIds': [self.vpn_id]})
        assert len(ret.response.VpnConnections) == 0

    def test_T3581_filters_virtual_gateway_ids_id1(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'VirtualGatewayIds': [self.vg_id]}).response.VpnConnections
        for vpn in ret:
            validate_vpn_connection(vpn, expected_vpn={'VirtualGatewayId': self.vg_id})

    def test_T3582_filters_virtual_gateway_ids_id2(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'VirtualGatewayIds': [self.vg_id2]}).response.VpnConnections
        for vpn in ret:
            validate_vpn_connection(vpn, expected_vpn={'VirtualGatewayId': self.vg_id2})

    def test_T5115_filters_tags(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={"Tags": ['toto=titi']}).response.VpnConnections
        assert len(ret) == 1

    def test_T5116_filters_tagkeys(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={"TagKeys": ['toto']}).response.VpnConnections
        assert len(ret) == 2

    def test_T5117_filters_tagvalues(self):
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={"TagValues": ['titi']}).response.VpnConnections
        assert len(ret) == 2

    def test_T5118_filters_invalid_tags(self):
        ret = self.a1_r1.oapi.ReadVpnConnections( Filters={"Tags": ['incorrect_vpn=incorrect_titi']}).response.VpnConnections
        assert len(ret) == 0

    def test_T5119_filters_incorrect_tags_type(self):
        try:
            self.a1_r1.oapi.ReadVpnConnections(Filters={"Tags": 'vpn=titi'})
            assert False, 'Remove known error'
            assert False, 'Call should fail'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5933_after_update(self):
        known_error('TINA-6738', 'On call intel.vpn.connection.update')
        self.a1_r1.oapi.UpdateVpnConnection(VpnConnectionId=self.vpn_id,
                               VpnOptions={"Phase1Options":{"DpdTimeoutAction":"test", "DpdTimeoutSeconds":1,"Phase1DhGroupNumbers":[1],
                                                            "Phase1EncryptionAlgorithms":["test"], "Phase1IntegrityAlgorithms":["test"],
                                                            "Phase1LifetimeSeconds":1, "ReplayWindowSize":1, "StartupAction":"xx"},
                                            "Phase2Options":{"Phase2DhGroupNumbers": [0], "Phase2EncryptionAlgorithms":
                                                             ["test"], "Phase2IntegrityAlgorithms": ["test"],
                                                             "Phase2LifetimeSeconds": 0, "PreSharedKey":"PreSharedKey"}})
        ret = self.a1_r1.oapi.ReadVpnConnections(Filters={'VpnConnectionIds': [self.vpn_id]})
# this will be changed by check oapi response
        assert hasattr(ret.response.VpnConnections[0], "VpnOptions")
        assert hasattr(ret.response.VpnConnections[0].VpnOptions, "Phase1Options")
        assert hasattr(ret.response.VpnConnections[0].VpnOptions, "Phase2Options")
        assert hasattr(ret.response.VpnConnections[0].VpnOptions.Phase1Options, "DpdTimeoutAction")
        assert hasattr(ret.response.VpnConnections[0].VpnOptions.Phase1Options, "DpdTimeoutSeconds")
        assert hasattr(ret.response.VpnConnections[0].VpnOptions.Phase1Options, "Phase1DhGroupNumbers")
        assert hasattr(ret.response.VpnConnections[0].VpnOptions.Phase1Options, "Phase1EncryptionAlgorithms")
        assert hasattr(ret.response.VpnConnections[0].VpnOptions.Phase1Options, "Phase1IntegrityAlgorithms")
        assert hasattr(ret.response.VpnConnections[0].VpnOptions.Phase1Options, "Phase1LifetimeSeconds")
        assert hasattr(ret.response.VpnConnections[0].VpnOptions.Phase1Options, "ReplayWindowSize")
        assert hasattr(ret.response.VpnConnections[0].VpnOptions.Phase1Options, "StartupAction")
        assert hasattr(ret.response.VpnConnections[0].VpnOptions.Phase2Options, "Phase2DhGroupNumbers")
        assert hasattr(ret.response.VpnConnections[0].VpnOptions.Phase2Options, "Phase2IntegrityAlgorithms")
        assert hasattr(ret.response.VpnConnections[0].VpnOptions.Phase2Options, "Phase2LifetimeSeconds")
        assert hasattr(ret.response.VpnConnections[0].VpnOptions.Phase2Options, "PreSharedKey")

    def test_T5983_with_tag_filter(self):
        misc.execute_tag_tests(self.a1_r1, 'VpnConnection', self.vpn_ids, 'oapi.ReadVpnConnections', 'VpnConnections.VpnConnectionId')
