from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import get_random_public_ip
from qa_tina_tools.tools.tina import wait_tools
from _curses import error
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_tina_tools.tina import wait


class Test_CreateVpnConnection(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'vpnc_limit': 1}
        super(Test_CreateVpnConnection, cls).setup_class()
        cls.cgw_id1 = None
        cls.vgw_id = None
        try:
            res = cls.a1_r1.fcu.CreateCustomerGateway(BgpAsn=65000, IpAddress=get_random_public_ip(), Type='ipsec.1')
            cls.cgw_id1 = res.response.customerGateway.customerGatewayId
            wait_tools.wait_customer_gateways_state(cls.a1_r1, [cls.cgw_id1], state='available')
            res = cls.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1')
            cls.vgw_id = res.response.vpnGateway.vpnGatewayId
            wait_tools.wait_vpn_gateways_state(cls.a1_r1, [cls.vgw_id], state='available')
        except Exception as error:
            try:
                cls.teardown_class()
            except:
                pass
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vgw_id:
                wait_tools.wait_vpn_gateways_state(cls.a1_r1, [cls.vgw_id], state='available')
                cls.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=cls.vgw_id)
                wait_tools.wait_vpn_gateways_state(cls.a1_r1, [cls.vgw_id], state='deleted')
            if cls.cgw_id1:
                wait_tools.wait_customer_gateways_state(cls.a1_r1, [cls.cgw_id1], state='available')
                cls.a1_r1.fcu.DeleteCustomerGateway(CustomerGatewayId=cls.cgw_id1)
                wait_tools.wait_customer_gateways_state(cls.a1_r1, [cls.cgw_id1], state='deleted')
        finally:
            super(Test_CreateVpnConnection, cls).teardown_class()

    def test_T4142_valid_params(self):
        vpn_connection_id = None
        try:
            res = self.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=self.cgw_id1, Type='ipsec.1', VpnGatewayId=self.vgw_id,
                                                     Options={'StaticRoutesOnly': True})
            vpn_connection_id = res.response.vpnConnection.vpnConnectionId
        finally:
            if vpn_connection_id:
                self.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn_connection_id)
                wait.wait_VpnConnections_state(self.a1_r1, [vpn_connection_id], state='deleted', cleanup=True)

    def test_T4143_missing_type(self):
        vpn_connection_id = None
        try:
            res = self.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=self.cgw_id1, VpnGatewayId=self.vgw_id, Options={'StaticRoutesOnly': True})
            vpn_connection_id = res.response.vpnConnection.vpnConnectionId
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "The request must contain the parameter: type")
        finally:
            if vpn_connection_id:
                self.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn_connection_id)
                wait.wait_VpnConnections_state(self.a1_r1, [vpn_connection_id], state='deleted', cleanup=True)

    def test_T4146_missing_vpn_gateway_id(self):
        vpn_connection_id = None
        try:
            res = self.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=self.cgw_id1, Type='ipsec.1', Options={'StaticRoutesOnly': True})
            vpn_connection_id = res.response.vpnConnection.vpnConnectionId
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "The request must contain the parameter: vpnGatewayId")
        finally:
            if vpn_connection_id:
                self.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn_connection_id)
                wait.wait_VpnConnections_state(self.a1_r1, [vpn_connection_id], state='deleted', cleanup=True)

    def test_T4148_missing_customer_gateway_id(self):
        vpn_connection_id = None
        try:
            res = self.a1_r1.fcu.CreateVpnConnection(Type='ipsec.1', VpnGatewayId=self.vgw_id, Options={'StaticRoutesOnly': True})
            vpn_connection_id = res.response.vpnConnection.vpnConnectionId
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "The request must contain the parameter: customerGatewayId")
        finally:
            if vpn_connection_id:
                self.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn_connection_id)
                wait.wait_VpnConnections_state(self.a1_r1, [vpn_connection_id], state='deleted', cleanup=True)

    def test_T3578_check_vpnc_per_vpng(self):
        vpn_connection_id = None
        cgw2_id = None
        vpn2_id = None
        try:
            res = self.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=self.cgw_id1, Type='ipsec.1', VpnGatewayId=self.vgw_id,
                                                     Options={'StaticRoutesOnly': True})
            vpn_connection_id = res.response.vpnConnection.vpnConnectionId
            ret = self.a1_r1.fcu.CreateCustomerGateway(BgpAsn=65000, IpAddress=get_random_public_ip(), Type='ipsec.1')
            cgw2_id = ret.response.customerGateway.customerGatewayId

            try:
                ret = self.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=cgw2_id,
                                                         Type='ipsec.1',
                                                         VpnGatewayId=self.vgw_id,
                                                         Options={'StaticRoutesOnly': True})
                vpn2_id = ret.response.vpnConnection.vpnConnectionId
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'VpnConnectionLimitExceeded', 'The limit has exceeded: 1.')

        except Exception as error:
            raise error
        finally:
            if vpn2_id:
                ret = self.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn2_id)
                wait.wait_VpnConnections_state(self.a1_r1, [vpn2_id], state='deleted', cleanup=True)
            if cgw2_id:
                self.a1_r1.fcu.DeleteCustomerGateway(CustomerGatewayId=cgw2_id)
                wait_tools.wait_customer_gateways_state(self.a1_r1, [cgw2_id], state='deleted')
            if vpn_connection_id:
                self.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn_connection_id)
                wait.wait_VpnConnections_state(self.a1_r1, [vpn_connection_id], state='deleted', cleanup=True)
