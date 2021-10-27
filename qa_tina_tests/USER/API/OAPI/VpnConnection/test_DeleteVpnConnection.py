

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tests.USER.API.OAPI.VpnConnection.VpnConnection import VpnConnection
from specs import check_oapi_error


class Test_DeleteVpnConnection(VpnConnection):

    def test_T3354_missing_parameter(self):
        try:
            self.a1_r1.oapi.DeleteVpnConnection()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T3355_invalid_vpn_connection_id(self):
        try:
            self.a1_r1.oapi.DeleteVpnConnection(VpnConnectionId='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='tata', prefixes='vpn-')
        try:
            self.a1_r1.oapi.DeleteVpnConnection(VpnConnectionId='vpn-1234567')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='vpn-1234567')
        try:
            self.a1_r1.oapi.DeleteVpnConnection(VpnConnectionId='vpn-123456789')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='vpn-123456789')
        try:
            self.a1_r1.oapi.DeleteVpnConnection(VpnConnectionId='vpn-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5067, id='vpn-12345678')

    def test_T3356_valid_case(self):
        self.a1_r1.oapi.DeleteVpnConnection(VpnConnectionId=self.vpn_id)
        self.vpn_id = None
