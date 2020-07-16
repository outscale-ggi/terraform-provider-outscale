from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import get_random_public_ip
from qa_tina_tools.tools.tina.wait_tools import wait_customer_gateways_state, wait_vpn_gateways_state, wait_vpn_connections_state
from _curses import error
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error


class Test_delete_recursive(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'vpnc_limit': 1}
        super(Test_delete_recursive, cls).setup_class()
        cls.cgw_id = None
        cls.vgw_id = None
        try:
            res = cls.a1_r1.fcu.CreateCustomerGateway(BgpAsn=65000, IpAddress=get_random_public_ip(), Type='ipsec.1')
            cls.cgw_id = res.response.customerGateway.customerGatewayId
            wait_customer_gateways_state(cls.a1_r1, [cls.cgw_id], state='available')
            res = cls.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1')
            cls.vgw_id = res.response.vpnGateway.vpnGatewayId
            wait_vpn_gateways_state(cls.a1_r1, [cls.vgw_id], state='available')
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
            pass
        finally:
            super(Test_delete_recursive, cls).teardown_class()

    def test_T5073_recursive_true(self):
        vpn_connection_id = None
        try:
            res = self.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=self.cgw_id, Type='ipsec.1', VpnGatewayId=self.vgw_id,
                                                     Options={'StaticRoutesOnly': True})
            vpn_connection_id = res.response.vpnConnection.vpnConnectionId
        finally:
            if vpn_connection_id:
                self.a1_r1.intel.vpn.virtual_private_gateway.delete(owner=self.a1_r1.config.account.account_id,
                                                                    id=vpn_connection_id, recursive=True)

                wait_vpn_connections_state(self.a1_r1, [vpn_connection_id], state='deleted')
                ret = self.a1_r1.fcu.DescribeVpnGateways()
                assert not ret.response.vpnGatewaySet
                ret = self.a1_r1.fcu.DescribeCustomerGateways()
                assert not ret.response.customerGatewaySet
