from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import get_random_public_ip
from qa_tina_tools.tools.tina.wait_tools import wait_customer_gateways_state, wait_vpn_gateways_state, wait_vpn_connections_state, wait_vpn_gateways_attachment_state
from _curses import error


class Test_delete_recursive(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'vpnc_limit': 1}
        super(Test_delete_recursive, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_delete_recursive, cls).teardown_class()

    def test_T5073_recursive_true(self):
        vpc_id = None
        vgw_id = None
        cgw_id = None
        vpn_conn_id = None
        try:
            vpc_id = self.a1_r1.fcu.CreateVpc(CidrBlock='10.0.0.0/16').response.vpc.vpcId
            vgw_id = self.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1').response.vpnGateway.vpnGatewayId
            wait_vpn_gateways_state(self.a1_r1, [vgw_id], state='available')
            self.a1_r1.fcu.AttachVpnGateway(VpcId=vpc_id, VpnGatewayId=vgw_id)
            wait_vpn_gateways_attachment_state(self.a1_r1, [vgw_id], 'attached')
            cgw_id = self.a1_r1.fcu.CreateCustomerGateway(BgpAsn=65000, IpAddress=get_random_public_ip(), Type='ipsec.1').response.customerGateway.customerGatewayId
            wait_customer_gateways_state(self.a1_r1, [cgw_id], state='available')
            vpn_conn_id = self.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=cgw_id, Type='ipsec.1', VpnGatewayId=vgw_id,
                                                             Options={'StaticRoutesOnly': True}).response.vpnConnection.vpnConnectionId

            self.a1_r1.intel.vpn.virtual_private_gateway.delete(owner=self.a1_r1.config.account.account_id, vpg_id=vgw_id, recursive=True)
            wait_vpn_connections_state(self.a1_r1, vpn_connection_id_list=[vpn_conn_id], state="deleted", wait_time=5, threshold=40)
            vpn_conn_id = None
            vgw_id = None
        except Exception as error:
            raise error
        finally:
            resp = self.a1_r1.fcu.DescribeCustomerGateways(CustomerGatewayId=[cgw_id]).response
            if resp.customerGatewaySet:
                try:
                    self.a1_r1.fcu.DeleteCustomerGateway(CustomerGatewayId=cgw_id)
                except:
                    pass
            resp = self.a1_r1.fcu.DescribeVpcs(VpcId=[vpc_id]).response
            if resp.vpcSet:
                try:
                    self.a1_r1.fcu.DeleteVpc(VpcId=[vpc_id])    
                except:
                    pass
            resp = self.a1_r1.fcu.DescribeVpnConnections(VpnConnectionId=[vpn_conn_id]).response
            assert not resp.vpnConnectionSet
            resp = self.a1_r1.fcu.DescribeVpnGateways(VpnGatewayId=[vgw_id]).response
            assert not resp.vpnGatewaySet
