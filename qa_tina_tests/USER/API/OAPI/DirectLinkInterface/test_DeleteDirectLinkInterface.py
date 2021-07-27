
import string

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, id_generator
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import wait


class Test_DeleteDirectLinkInterface(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        cls.virtual_gateway_id = None
        super(Test_DeleteDirectLinkInterface, cls).setup_class()
        try:
            cls.virtual_gateway_id = cls.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.virtual_gateway_id:
                cls.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=cls.virtual_gateway_id)
        finally:
            super(Test_DeleteDirectLinkInterface, cls).teardown_class()

    def test_T3911_empty_param(self):
        try:
            self.a1_r1.oapi.DeleteDirectLinkInterface()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    def test_T3912_invalid_direct_link_interface_id(self):
        try:
            self.a1_r1.oapi.DeleteDirectLinkInterface(DirectLinkInterfaceId='id_invalid')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104', None)
        try:
            self.a1_r1.oapi.DeleteDirectLinkInterface(DirectLinkInterfaceId='dxvif-1234567')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105', None)
        try:
            self.a1_r1.oapi.DeleteDirectLinkInterface(DirectLinkInterfaceId='dxvif-123456789')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105', None)

    def test_T3913_unknown_direct_link_interface_id(self):
        try:
            self.a1_r1.oapi.DeleteDirectLinkInterface(DirectLinkInterfaceId='dxvif-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5073', None)

    @pytest.mark.region_admin
    @pytest.mark.region_directlink
    def test_T4074_valid_params(self):
        known_error('GTW-2012', 'Incorrect response structure')
        known_error('GTW-2013', 'Incorrect response structure')
        ret_dl = None
        ret_dli = None
        directlink_interface_id = None
        try:
            direct_link_interface_name = id_generator(size=10, chars=string.ascii_lowercase)
            direct_link_name = id_generator(size=8, chars=string.ascii_lowercase)
            location_var = self.a1_r1.oapi.ReadLocations().response.Locations[0].Code
            ret_dl = self.a1_r1.oapi.CreateDirectLink(DirectLinkName=direct_link_name, Location=location_var, Bandwidth='1Gbps')
            wait.wait_DirectLinks_state(self.a1_r1, [ret_dl.response.DirectLink.DirectLinkId], state="pending")
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id,
                                                    connection_id=ret_dl.response.DirectLink.DirectLinkId)
            wait.wait_DirectLinks_state(self.a1_r1, [ret_dl.response.DirectLink.DirectLinkId], state="available")
            ret_dli = self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId=ret_dl.response.DirectLink.DirectLinkId,
                                                                     DirectLinkInterface={'BgpAsn': 1, 'Vlan': 2,
                                                                                          'VirtualGatewayId': self.virtual_gateway_id,
                                                                                          'DirectLinkInterfaceName': direct_link_interface_name})
            directlink_interface_id = ret_dli.response.DirectLinkInterfaces.DirectLinkInterfaceId
            wait.wait_DirectLinkInterfaces_state(self.a1_r1, [directlink_interface_id], state='available')
            self.a1_r1.oapi.DeleteDirectLinkInterface(DirectLinkInterfaceId=directlink_interface_id)
            ret_dli = None
            wait.wait_DirectLinkInterfaces_state(self.a1_r1, [directlink_interface_id], state='deleted')
        finally:
            if ret_dli:
                self.a1_r1.oapi.DeleteDirectLinkInterface(DirectLinkInterfaceId=directlink_interface_id)
                wait.wait_DirectLinkInterfaces_state(self.a1_r1, [directlink_interface_id], state='deleted')
            if ret_dl:
                self.a1_r1.oapi.DeleteDirectLink(DirectLinkId=ret_dl.response.DirectLink.DirectLinkId)

    @pytest.mark.region_admin
    @pytest.mark.region_directlink
    def test_T4075_with_another_account(self):
        known_error('GTW-2012', 'Incorrect response structure')
        known_error('GTW-2013', 'Incorrect response structure')
        ret_dli = None
        directlink_interface_id = None
        try:
            direct_link_interface_name = id_generator(size=10, chars=string.ascii_lowercase)
            direct_link_name = id_generator(size=8, chars=string.ascii_lowercase)
            location_var = self.a1_r1.oapi.ReadLocations().response.Locations[0].Code
            ret_dl = self.a1_r1.oapi.CreateDirectLink(DirectLinkName=direct_link_name, Location=location_var, Bandwidth='1Gbps')
            wait.wait_DirectLinks_state(self.a1_r1, [ret_dl.response.DirectLink.DirectLinkId], state="pending")
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id,
                                                    connection_id=ret_dl.response.DirectLink.DirectLinkId)
            wait.wait_DirectLinks_state(self.a1_r1, [ret_dl.response.DirectLink.DirectLinkId], state="available")
            ret_dli = self.a1_r1.oapi.CreateDirectLinkInterface(DirectLinkId=ret_dl.response.DirectLink.DirectLinkId,
                                                                     DirectLinkInterface={'BgpAsn': 1, 'Vlan': 2,
                                                                                          'VirtualGatewayId': self.virtual_gateway_id,
                                                                                          'DirectLinkInterfaceName': direct_link_interface_name})
            directlink_interface_id = ret_dli.response.DirectLinkInterfaces.DirectLinkInterfaceId
            wait.wait_DirectLinkInterfaces_state(self.a1_r1, [directlink_interface_id], state='available')
            self.a2_r1.oapi.DeleteDirectLinkInterface(DirectLinkInterfaceId=directlink_interface_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, '', '', None)
        finally:
            if ret_dli:
                self.a1_r1.oapi.DeleteDirectLinkInterface(DirectLinkInterfaceId=directlink_interface_id)
                wait.wait_DirectLinkInterfaces_state(self.a1_r1, [directlink_interface_id], state='deleted')
            if ret_dl:
                self.a1_r1.oapi.DeleteDirectLink(DirectLinkId=ret_dl.response.DirectLink.DirectLinkId)
