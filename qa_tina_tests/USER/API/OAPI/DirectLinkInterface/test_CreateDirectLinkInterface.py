# -*- coding:utf-8 -*-
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, id_generator
from qa_test_tools.test_base import OscTestSuite
import string
import pytest


class Test_CreateDirectLinkInterface(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        cls.virtual_gateway_id = None
        super(Test_CreateDirectLinkInterface, cls).setup_class()
        try:
            cls.virtual_gateway_id = cls.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.virtual_gateway_id:
                cls.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=cls.virtual_gateway_id)
        finally:
            super(Test_CreateDirectLinkInterface, cls).teardown_class()

    def test_T3906_empty_param(self):
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    @pytest.mark.region_directlink
    def test_T4073_valid_params(self):
        pytest.skip('Test must be implemented')
        direct_link_interface_name = id_generator(size=10, chars=string.ascii_lowercase)
        direct_link_name = id_generator(size=8, chars=string.ascii_lowercase)
        location_var = self.a1_r1.oapi.ReadLocations().response.Locations[0].Code
        ret = self.a1_r1.oapi.CreateDirectLink(DirectLinkName=direct_link_name, Location=location_var, Bandwidth='1Gbps')
        direct_link_id = ret.response.DirectLink.DirectLinkId
        self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId=direct_link_id,
                                                  DirectLinkInterface={'BgpAsn': 1, 'Vlan': 1, 'VirtualGatewayId': self.virtual_gateway_id,
                                                                       'DirectLinkInterfaceName': direct_link_interface_name})

    def test_T3907_missing_parameters(self):
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId='dxcon-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkInterface={'BgpAsn': 1})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkInterface={'Vlan': 1})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkInterface={'VirtualGatewayId': self.virtual_gateway_id})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkInterface={'DirectLinkInterfaceName': 'a_name'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId='dxcon-12345678',
                                                      DirectLinkInterface={'VirtualGatewayId': self.virtual_gateway_id})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId='dxcon-12345678',
                                                      DirectLinkInterface={'Vlan': 1, 'VirtualGatewayId': self.virtual_gateway_id})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId='dxcon-12345678',
                                                      DirectLinkInterface={'BgpAsn': 1, 'VirtualGatewayId': self.virtual_gateway_id})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId='dxcon-12345678',
                                                      DirectLinkInterface={'VirtualGatewayId': self.virtual_gateway_id,
                                                                           'DirectLinkInterfaceName': 'a_name'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    def test_T3908_invalid_direct_link_id(self):
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId='tests',
                                                      DirectLinkInterface={'BgpAsn': 1, 'Vlan': 2, 'VirtualGatewayId': self.virtual_gateway_id})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104', None)
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId='dxcon-1234567',
                                                      DirectLinkInterface={'BgpAsn': 1, 'Vlan': 2, 'VirtualGatewayId': self.virtual_gateway_id,
                                                                           'DirectLinkInterfaceName': 'a_name'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105', None)
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId='dxcon-123456789',
                                                      DirectLinkInterface={'BgpAsn': 1, 'Vlan': 2, 'VirtualGatewayId': self.virtual_gateway_id,
                                                                           'DirectLinkInterfaceName': 'a_name'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105', None)

    def test_T3909_unknown_direct_link_id(self):
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId='dxcon-12345678',
                                                      DirectLinkInterface={'BgpAsn': 1, 'Vlan': 2, 'VirtualGatewayId': self.virtual_gateway_id,
                                                                           'DirectLinkInterfaceName': 'a_name'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5072', None)

    def test_T3910_invalid_virtual_gateway_id(self):
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId='dxcon-12345678',
                                                      DirectLinkInterface={'BgpAsn': 1, 'Vlan': 2, 'VirtualGatewayId': 'test'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104', None)
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId='dxcon-12345678',
                                                      DirectLinkInterface={'BgpAsn': 1, 'Vlan': 2, 'VirtualGatewayId': 'vgw-1234567'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105', None)
        try:
            self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId='dxcon-12345678',
                                                      DirectLinkInterface={'BgpAsn': 1, 'Vlan': 2, 'VirtualGatewayId': 'vgw-123456789'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105', None)
