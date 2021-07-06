import os

from specs.check_tools import check_oapi_error
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.compare_objects import verify_response, create_hints
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
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpn_id:
                cls.a1_r1.oapi.DeleteVpnConnection(VpnConnectionId=cls.vpn_id)
                wait.wait_VpnConnections_state(cls.a1_r1, [cls.vpn_id], state='deleted', cleanup=True)
        except:
            print('Could not delete vpn connection')
        try:
            if cls.vg_id:
                cls.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=cls.vg_id)
        except:
            print('Could not delete virtual gateway')
        try:
            if cls.cg_id:
                cls.a1_r1.oapi.DeleteClientGateway(ClientGatewayId=cls.cg_id)
        except:
            print('Could not delete client gateway')
        finally:
            super(Test_CreateVpnConnection, cls).teardown_class()

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
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateVpnConnection(ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateVpnConnection(ConnectionType='ipsec.1', ClientGatewayId=self.cg_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateVpnConnection(ConnectionType='ipsec.1', VirtualGatewayId=self.vg_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id, VirtualGatewayId=self.vg_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T3345_invalid_connection_type(self):
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id, VirtualGatewayId=self.vg_id, ConnectionType='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4047)

    def test_T3346_invalid_client_gateway_id(self):
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId='tata', VirtualGatewayId=self.vg_id, ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='tata', prefixes='cgw-')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId='cgw-1234567', VirtualGatewayId=self.vg_id, ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='cgw-1234567')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId='cgw-123456789', VirtualGatewayId=self.vg_id, ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='cgw-123456789')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId='cgw-12345678', VirtualGatewayId=self.vg_id, ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5015, id='cgw-12345678')

    def test_T3347_invalid_virtual_gateway_id(self):
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id, VirtualGatewayId='tata', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='tata', prefixes='vgw-')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id, VirtualGatewayId='vgw-1234567', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='vgw-1234567')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id, VirtualGatewayId='vgw-123456789', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='vgw-123456789')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id, VirtualGatewayId='vgw-12345678', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5068, id='vgw-12345678')
        try:
            self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.vg_id, VirtualGatewayId=self.cg_id, ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid=self.vg_id, prefixes='cgw-')

    def test_T3348_valid_case(self):
        hints = []
        ret = self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id,
                                                  VirtualGatewayId=self.vg_id,
                                                  ConnectionType='ipsec.1')

        self.vpn_id = ret.response.VpnConnection.VpnConnectionId

        hints.append(ret.response.VpnConnection.ClientGatewayId)
        hints.append(ret.response.VpnConnection.ConnectionType)
        hints.append(str(ret.response.VpnConnection.StaticRoutesOnly))
        hints.append(ret.response.VpnConnection.VirtualGatewayId)
        hints.append(ret.response.VpnConnection.VpnConnectionId)

        hints = create_hints(hints)

        verify_response(ret.response,
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T3348_vpn_connection_with_required_param.json'),
                        hints,
                        ignored_keys="ClientGatewayConfiguration")

        if self.vpn_id:
            try:
                self.a1_r1.oapi.DeleteVpnConnection(VpnConnectionId=self.vpn_id)
                wait.wait_VpnConnections_state(self.a1_r1, [self.vpn_id], state='deleted', cleanup=True)
            except:
                print('Could not delete vpn connection')

    def test_T5730_vpn_connection_dry_run(self):
        ret = self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id,
                                                  VirtualGatewayId=self.vg_id,
                                                  ConnectionType='ipsec.1',
                                                  DryRun=True)
        assert_dry_run(ret)

    def test_T5731_vpn_connection_static_routes(self):
        hints = []
        ret = self.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=self.cg_id,
                                                  VirtualGatewayId=self.vg_id,
                                                  ConnectionType='ipsec.1',
                                                  StaticRoutesOnly=True)

        self.vpn_id = ret.response.VpnConnection.VpnConnectionId
        self.a1_r1.oapi.CreateVpnConnectionRoute(VpnConnectionId=self.vpn_id, DestinationIpRange='172.13.1.4/24')

        hints.append(ret.response.VpnConnection.ClientGatewayId)
        hints.append(ret.response.VpnConnection.ConnectionType)
        hints.append(str(ret.response.VpnConnection.StaticRoutesOnly))
        hints.append(ret.response.VpnConnection.VirtualGatewayId)
        hints.append(ret.response.VpnConnection.VpnConnectionId)

        hints = create_hints(hints)

        verify_response(ret.response,
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T5731_vpn_connection_with_static_routes_only.json'),
                        hints,
                        ignored_keys="ClientGatewayConfiguration")

        if self.vpn_id:
            try:
                self.a1_r1.oapi.DeleteVpnConnectionRoute(VpnConnectionId=self.vpn_id, DestinationIpRange='172.13.1.4/24')

                self.a1_r1.oapi.DeleteVpnConnection(VpnConnectionId=self.vpn_id)

                wait.wait_VpnConnections_state(self.a1_r1, [self.vpn_id], state='deleted', cleanup=True)
            except:
                print('Could not delete vpn connection')
