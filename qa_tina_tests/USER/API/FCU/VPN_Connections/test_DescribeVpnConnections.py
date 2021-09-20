from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import wait
from qa_tina_tools.tools.tina import wait_tools
from qa_tina_tools.tools.tina import create_tools, delete_tools
from qa_tina_tools.tools.tina import info_keys
from qa_tina_tools.tools.tina.wait_tools import wait_vpn_gateways_attachment_state,\
    wait_customer_gateways_state, wait_vpn_connections_state

NUM_VPN_CONNS = 4


class Test_DescribeVpnConnections(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeVpnConnections, cls).setup_class()
        cls.inst_cgw_info = None
        cls.vpc_info = None
        cls.cgw_ids = []
        cls.vgw_id = None
        cls.vpn_connection_ids = []
        cls.ret_attach = None
        try:
            # create a pub instance for the CGW
            cls.inst_cgw_info = create_tools.create_instances(osc_sdk=cls.a1_r1, nb=NUM_VPN_CONNS)
            for i in range(NUM_VPN_CONNS):
                # create CGW with pub instance IP
                ret = cls.a1_r1.fcu.CreateCustomerGateway(BgpAsn=65000, IpAddress=cls.inst_cgw_info[info_keys.INSTANCE_SET][i]['ipAddress'],
                                                          Type='ipsec.1')
                wait_customer_gateways_state(cls.a1_r1, [ret.response.customerGateway.customerGatewayId], state='available')
                cls.cgw_ids.append(ret.response.customerGateway.customerGatewayId)
            # create and attach VGW
            ret = cls.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1')
            cls.vgw_id = ret.response.vpnGateway.vpnGatewayId
            cls.vpc_info = create_tools.create_vpc(osc_sdk=cls.a1_r1, nb_instance=1, default_rtb=True)
            cls.ret_attach = cls.a1_r1.fcu.AttachVpnGateway(VpcId=cls.vpc_info[info_keys.VPC_ID], VpnGatewayId=cls.vgw_id)
            wait_vpn_gateways_attachment_state(cls.a1_r1, [cls.vgw_id], 'attached')
            # create VPN connection
            for i in range(NUM_VPN_CONNS):
                ret = cls.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=cls.cgw_ids[i],
                                                        Type='ipsec.1',
                                                        VpnGatewayId=cls.vgw_id,
                                                        Options={'StaticRoutesOnly': True})
                wait_vpn_connections_state(cls.a1_r1, [ret.response.vpnConnection.vpnConnectionId], state='available')
                cls.vpn_connection_ids.append(ret.response.vpnConnection.vpnConnectionId)
        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            # delete all created resources in setup
            for vpn_conn_id in cls.vpn_connection_ids:
                cls.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn_conn_id)
                wait.wait_VpnConnections_state(cls.a1_r1, [vpn_conn_id], state='deleted', cleanup=True)
            if cls.vgw_id:
                if cls.ret_attach:
                    cls.a1_r1.fcu.DetachVpnGateway(VpcId=cls.vpc_info[info_keys.VPC_ID], VpnGatewayId=cls.vgw_id)
                    wait_tools.wait_vpn_gateways_attachment_state(cls.a1_r1, [cls.vgw_id], 'detached')
                cls.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=cls.vgw_id)
                wait_tools.wait_vpn_gateways_state(cls.a1_r1, [cls.vgw_id], state='deleted')
            if cls.cgw_ids:
                for cgw_id in cls.cgw_ids:
                    cls.a1_r1.fcu.DeleteCustomerGateway(CustomerGatewayId=cgw_id)
                wait_tools.wait_customer_gateways_state(cls.a1_r1, cls.cgw_ids, state='deleted')
            if cls.vpc_info:
                delete_tools.delete_vpc(cls.a1_r1, cls.vpc_info)
            if cls.inst_cgw_info:
                delete_tools.delete_instances(cls.a1_r1, cls.inst_cgw_info)
        except Exception as error:
            raise error
        finally:
            super(Test_DescribeVpnConnections, cls).teardown_class()

    # DryRun, Filter.N, VpnConnectionId.N

    def test_T3277_no_params(self):
        ret = self.a1_r1.fcu.DescribeVpnConnections()
        assert len({vpnconn.vpnConnectionId for vpnconn in ret.response.vpnConnectionSet}) == NUM_VPN_CONNS
        for vpnconn in ret.response.vpnConnectionSet:
            assert vpnconn.vpnConnectionId in self.vpn_connection_ids

    def test_T3278_dry_run(self):
        try:
            self.a1_r1.fcu.DescribeVpnConnections(DryRun=True)
        except OscApiException as error:
            misc.assert_error(error, 400, 'DryRunOperation', 'Request would have succeeded, but DryRun flag is set.')

    def test_T3279_from_other_account(self):
        try:
            self.a2_r1.fcu.DescribeVpnConnections(VpnConnectionId=[self.vpn_connection_ids[0]])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, 'InvalidVpnConnectionID.NotFound',
                              'The VpnConnection ID {} does not exist'.format(self.vpn_connection_ids[0]))

    def test_T3280_with_id(self):
        ret = self.a1_r1.fcu.DescribeVpnConnections(VpnConnectionId=[self.vpn_connection_ids[0]])
        assert len(ret.response.vpnConnectionSet) == 1
        assert ret.response.vpnConnectionSet[0].vpnConnectionId == self.vpn_connection_ids[0]

    def test_T3281_with_filter_vpn_connection_id(self):
        ret = self.a1_r1.fcu.DescribeVpnConnections(Filter=[{'Name': 'vpn-connection-id', 'Value': [self.vpn_connection_ids[0]]}])
        assert len(ret.response.vpnConnectionSet) == 1
        assert ret.response.vpnConnectionSet[0].vpnConnectionId == self.vpn_connection_ids[0]

    def test_T5964_with_tag_filter(self):
        misc.execute_tag_tests(self.a1_r1, 'VpnConnection', self.vpn_connection_ids,
                               'fcu.DescribeVpnConnections', 'vpnConnectionSet.vpnConnectionId')
