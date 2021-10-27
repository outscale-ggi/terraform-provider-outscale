

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from specs import check_oapi_error
from qa_tina_tests.USER.API.OAPI.VpnConnection.VpnConnection import VpnConnection


class Test_DeleteVpnConnectionRoute(VpnConnection):

    def test_T3357_missing_parameter(self):
        try:
            self.a1_r1.oapi.DeleteVpnConnectionRoute()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.DeleteVpnConnectionRoute(DestinationIpRange='172.13.1.4/24')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.DeleteVpnConnectionRoute(VpnConnectionId='vpn-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T3358_invalid_vpn_connection_id(self):
        try:
            self.a1_r1.oapi.DeleteVpnConnectionRoute(VpnConnectionId='tata', DestinationIpRange='172.13.1.4/24')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='tata', prefixes='vpn-')
        try:
            self.a1_r1.oapi.DeleteVpnConnectionRoute(VpnConnectionId='vpn-1234567', DestinationIpRange='172.13.1.4/24')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='vpn-1234567')
        try:
            self.a1_r1.oapi.DeleteVpnConnectionRoute(VpnConnectionId='vpn-123456789', DestinationIpRange='172.13.1.4/24')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='vpn-123456789')
        try:
            self.a1_r1.oapi.DeleteVpnConnectionRoute(VpnConnectionId='vpn-12345678', DestinationIpRange='172.13.1.4/24')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5067, id='vpn-12345678')

    def test_T3359_static_routes_non_active(self):
        try:
            self.a1_r1.oapi.DeleteVpnConnectionRoute(VpnConnectionId=self.vpn_id2, DestinationIpRange='0.13.1.4/24')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 9068)

    def test_T3360_invalid_destination_ip_range(self):
        try:
            self.a1_r1.oapi.DeleteVpnConnectionRoute(VpnConnectionId=self.vpn_id, DestinationIpRange='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4047)

    def test_T3361_unknown_route(self):
        try:
            self.a1_r1.oapi.DeleteVpnConnectionRoute(VpnConnectionId=self.vpn_id, DestinationIpRange='172.16.1.4/24')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5055, id=self.vpn_id)

    def test_T3362_valid_case(self):
        self.a1_r1.oapi.CreateVpnConnectionRoute(VpnConnectionId=self.vpn_id, DestinationIpRange='172.13.1.4/24')
        self.a1_r1.oapi.DeleteVpnConnectionRoute(VpnConnectionId=self.vpn_id, DestinationIpRange='172.13.1.4/24')
