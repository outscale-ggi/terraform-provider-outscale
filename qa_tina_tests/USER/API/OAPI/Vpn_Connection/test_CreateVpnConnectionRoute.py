# -*- coding:utf-8 -*-
# -*- coding:utf-8 -*-

from osc_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tests.USER.API.OAPI.Vpn_Connection.VpnConnection import VpnConnection
from qa_common_tools.misc import assert_oapi_error


class Test_CreateVpnConnectionRoute(VpnConnection):

    def test_T3349_missing_parameter(self):
        try:
            self.a1_r1.oapi.CreateVpnConnectionRoute()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateVpnConnectionRoute(DestinationIpRange='172.13.1.4/24')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateVpnConnectionRoute(VpnConnectionId='vpn-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T3350_invalid_vpn_connection_id(self):
        try:
            self.a1_r1.oapi.CreateVpnConnectionRoute(VpnConnectionId='tata', DestinationIpRange='172.13.1.4/24')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')
        try:
            self.a1_r1.oapi.CreateVpnConnectionRoute(VpnConnectionId='vpn-1234567', DestinationIpRange='172.13.1.4/24')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')
        try:
            self.a1_r1.oapi.CreateVpnConnectionRoute(VpnConnectionId='vpn-123456789', DestinationIpRange='172.13.1.4/24')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')
        try:
            self.a1_r1.oapi.CreateVpnConnectionRoute(VpnConnectionId='vpn-12345678', DestinationIpRange='172.13.1.4/24')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5067')

    def test_T3351_static_routes_non_active(self):
        try:
            self.a1_r1.oapi.CreateVpnConnectionRoute(VpnConnectionId=self.vpn_id2, DestinationIpRange='0.13.1.4/24')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9068')

    def test_T3352_invalid_destination_ip_range(self):
        try:
            self.a1_r1.oapi.CreateVpnConnectionRoute(VpnConnectionId=self.vpn_id, DestinationIpRange='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T3353_valid_case(self):
        self.a1_r1.oapi.CreateVpnConnectionRoute(VpnConnectionId=self.vpn_id, DestinationIpRange='172.13.1.4/24')
