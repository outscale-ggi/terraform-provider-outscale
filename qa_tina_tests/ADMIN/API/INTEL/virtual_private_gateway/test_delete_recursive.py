from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.wait import wait_VpnConnections_state
from qa_tina_tools.tools.tina.create_tools import get_random_public_ip
from qa_tina_tools.tools.tina.wait_tools import wait_customer_gateways_state, wait_vpn_gateways_state, wait_vpn_gateways_attachment_state, \
    wait_vpn_connections_state


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
            wait_vpn_connections_state(self.a1_r1, [vpn_conn_id], state='available')

            self.a1_r1.intel.vpn.virtual_private_gateway.delete(owner=self.a1_r1.config.account.account_id, vpg_id=vgw_id, recursive=True)
            wait_VpnConnections_state(self.a1_r1, [vpn_conn_id], state='deleted')
            vpn_conn_id = None
            vgw_id = None
        except Exception as error:
            raise error
        finally:
            if vpn_conn_id:
                try:
                    self.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn_conn_id)
                    wait_VpnConnections_state(self.a1_r1, [vpn_conn_id], 'deleted')
                except:
                    pass
            if vgw_id:
                try:
                    self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=vgw_id)
                except:
                    pass
            resp = self.a1_r1.fcu.DescribeCustomerGateways(CustomerGatewayId=[cgw_id]).response
            if resp.customerGatewaySet:
                try:
                    self.a1_r1.fcu.DeleteCustomerGateway(CustomerGatewayId=cgw_id)
                except:
                    pass
            resp = self.a1_r1.fcu.DescribeVpcs(VpcId=[vpc_id]).response
            if resp.vpcSet:
                try:
                    self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)    
                except:
                    pass
            resp = self.a1_r1.fcu.DescribeVpnConnections().response
            states = set([v.state for v in resp.vpnConnectionSet])
            assert not resp.vpnConnectionSet or (len(states) == 1 and states.pop() == 'deleted')
            resp = self.a1_r1.fcu.DescribeVpnGateways().response
            states = set([v.state for v in resp.vpnGatewaySet])
            assert not resp.vpnGatewaySet or (len(states) == 1 and states.pop() == 'deleted')
