# -*- coding:utf-8 -*-
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tests.USER.API.OAPI.VpnConnection.VpnConnection import validate_vpn_connection
from qa_test_tools.misc import  assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.config.configuration import Configuration
from qa_tina_tools.tina import wait


class Test_CreateVpnConnection(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateVpnConnection, cls).setup_class()
        cls.vg_id = None
        cls.cg_id = None
        cls.cg_id_dependency_problem = None
        cls.vpn_id = None
        try:
            # Virtual Gateway
            cls.vg_id = cls.a1_r1.oapi.CreateVirtualGateway(
                ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
            # Client Gateway
            cls.cgw_ip = Configuration.get('ipaddress', 'cgw_ip')
            cls.cg_id = cls.a1_r1.oapi.CreateClientGateway(
                BgpAsn=65000, PublicIp=cls.cgw_ip, ConnectionType='ipsec.1').response.ClientGateway.ClientGatewayId
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpn_id:
                cls.a1_r1.oapi.DeleteVpnConnection(VpnConnectionId=cls.vpn_id)
                wait.wait_VpnConnections_state(cls.a1_r1, [cls.vpn_id], state='deleted', cleanup=True)
        except:
            pass
        try:
            if cls.vg_id:
                cls.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=cls.vg_id)
        except:
            pass
        try:
            if cls.cg_id:
                cls.a1_r1.oapi.DeleteClientGateway(ClientGatewayId=cls.cg_id)
        except:
            pass
        finally:
            super(Test_CreateVpnConnection, cls).teardown_class()

    def setup_method(self, method):
        super(Test_CreateVpnConnection, self).setup_method(method)

    def teardown_method(self, method):
        try:
            if self.vpn_id:
                self.a1_r1.oapi.DeleteVpnConnection(VpnConnectionId=self.vpn_id)
                wait.wait_VpnConnections_state(self.a1_r1, [self.vpn_id], state='deleted', cleanup=True)
        finally:
            super(Test_CreateVpnConnection, self).teardown_method(method)

    def test_T3344_missing_parameter(self):
        try:
            self.a1_r1.oapi.CreateVpnConnection()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ConnectionType='ipsec.1', ClientGatewayId=self.cg_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ConnectionType='ipsec.1', VirtualGatewayId=self.vg_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id, VirtualGatewayId=self.vg_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T3345_invalid_connection_type(self):
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id, VirtualGatewayId=self.vg_id, ConnectionType='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T3346_invalid_client_gateway_id(self):
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId='tata', VirtualGatewayId=self.vg_id, ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId='cgw-1234567', VirtualGatewayId=self.vg_id, ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId='cgw-123456789', VirtualGatewayId=self.vg_id, ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId='cgw-12345678', VirtualGatewayId=self.vg_id, ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5015')

    def test_T3347_invalid_virtual_gateway_id(self):
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id, VirtualGatewayId='tata', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id, VirtualGatewayId='vgw-1234567', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id, VirtualGatewayId='vgw-123456789', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id, VirtualGatewayId='vgw-12345678', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5068')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.vg_id, VirtualGatewayId=self.cg_id, ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T3348_valid_case(self):
        ret = self.a1_r1.oapi.CreateVpnConnection(
            ClientGatewayId=self.cg_id, VirtualGatewayId=self.vg_id, ConnectionType='ipsec.1').response.VpnConnection
        self.vpn_id = ret.VpnConnectionId
        validate_vpn_connection(ret, expected_vpn={
            'ClientGatewayId': self.cg_id,
            'VirtualGatewayId': self.vg_id,
            'ConnectionType': 'ipsec.1',
        })
        assert hasattr(ret, 'ClientGatewayConfiguration')

