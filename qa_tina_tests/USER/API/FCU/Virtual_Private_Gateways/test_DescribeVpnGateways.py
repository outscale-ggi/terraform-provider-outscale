from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_tina_tools.tools.tina.wait_tools import wait_vpn_gateways_attachment_state, wait_vpn_gateways_state


class Test_DescribeVpnGateways(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_infos = []
        cls.vgw_id1 = None
        cls.vgw_id2 = None
        cls.ret_attach1 = None
        cls.ret_attach2 = None
        super(Test_DescribeVpnGateways, cls).setup_class()
        try:
            cls.vgw_id1 = cls.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1').response.vpnGateway.vpnGatewayId
            cls.vgw_id2 = cls.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1').response.vpnGateway.vpnGatewayId
            cls.vpc_infos.append(create_vpc(osc_sdk=cls.a1_r1))
            cls.vpc_infos.append(create_vpc(osc_sdk=cls.a1_r1))
            cls.ret_attach1 = cls.a1_r1.fcu.AttachVpnGateway(VpcId=cls.vpc_infos[0][VPC_ID], VpnGatewayId=cls.vgw_id1)
            cls.ret_attach2 = cls.a1_r1.fcu.AttachVpnGateway(VpcId=cls.vpc_infos[1][VPC_ID], VpnGatewayId=cls.vgw_id2)
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vgw_id1:
                if cls.ret_attach1:
                    cls.a1_r1.fcu.DetachVpnGateway(VpcId=cls.vpc_infos[0][VPC_ID], VpnGatewayId=cls.vgw_id1)
                    wait_vpn_gateways_attachment_state(cls.a1_r1, [cls.vgw_id1], 'detached')
                cls.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=cls.vgw_id1)
                wait_vpn_gateways_state(cls.a1_r1, [cls.vgw_id1], state='deleted')
            if cls.vgw_id2:
                if cls.ret_attach2:
                    cls.a1_r1.fcu.DetachVpnGateway(VpcId=cls.vpc_infos[1][VPC_ID], VpnGatewayId=cls.vgw_id2)
                    wait_vpn_gateways_attachment_state(cls.a1_r1, [cls.vgw_id2], 'detached')
                cls.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=cls.vgw_id2)
                wait_vpn_gateways_state(cls.a1_r1, [cls.vgw_id2], state='deleted')
            if cls.vpc_infos:
                for vpc_info in cls.vpc_infos:
                    delete_vpc(cls.a1_r1, vpc_info)
        finally:
            super(Test_DescribeVpnGateways, cls).teardown_class()

    def test_T3586_with_attachment_vpc_filter(self):
        ret = self.a1_r1.fcu.DescribeVpnGateways(Filter=[{'Name': 'attachment.vpc-id', 'Value': [self.vpc_infos[0][VPC_ID]]}])
        assert len(ret.response.vpnGatewaySet) == 1 and ret.response.vpnGatewaySet[0].vpnGatewayId == self.vgw_id1
