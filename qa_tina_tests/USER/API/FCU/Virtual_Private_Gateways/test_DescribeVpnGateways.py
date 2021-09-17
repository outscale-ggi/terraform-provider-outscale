
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina import create_tools, delete_tools, info_keys, wait_tools

NUM_VPN_GTW = 4


class Test_DescribeVpnGateways(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.vpc_infos = []
        cls.vgw_ids = []
        cls.ret_attach = []
        super(Test_DescribeVpnGateways, cls).setup_class()
        try:
            for _ in range(NUM_VPN_GTW):
                cls.vgw_ids.append(cls.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1').response.vpnGateway.vpnGatewayId)
            for _ in range(NUM_VPN_GTW):
                cls.vpc_infos.append(create_tools.create_vpc(osc_sdk=cls.a1_r1))
            for i in range(NUM_VPN_GTW):
                cls.ret_attach.append(cls.a1_r1.fcu.AttachVpnGateway(VpcId=cls.vpc_infos[i][info_keys.VPC_ID], VpnGatewayId=cls.vgw_ids[i]))
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            for i in range(NUM_VPN_GTW):
                if len(cls.ret_attach) > i:
                    cls.a1_r1.fcu.DetachVpnGateway(VpcId=cls.vpc_infos[i][info_keys.VPC_ID], VpnGatewayId=cls.vgw_ids[i])
                    wait_tools.wait_vpn_gateways_attachment_state(cls.a1_r1, [cls.vgw_ids[i]], 'detached')
                cls.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=cls.vgw_ids[i])
                wait_tools.wait_vpn_gateways_state(cls.a1_r1, [cls.vgw_ids[i]], state='deleted')
            for vpc_info in cls.vpc_infos:
                delete_tools.delete_vpc(cls.a1_r1, vpc_info)
        finally:
            super(Test_DescribeVpnGateways, cls).teardown_class()

    def test_T3586_with_attachment_vpc_filter(self):
        ret = self.a1_r1.fcu.DescribeVpnGateways(Filter=[{'Name': 'attachment.vpc-id', 'Value': [self.vpc_infos[0][info_keys.VPC_ID]]}])
        assert len(ret.response.vpnGatewaySet) == 1 and ret.response.vpnGatewaySet[0].vpnGatewayId == self.vgw_ids[0]

    def test_T5965_with_tag_filter(self):
        indexes, _ = misc.execute_tag_tests(self.a1_r1, 'VpnGateway', self.vgw_ids,
                               'fcu.DescribeVpnGateways', 'vpnGatewaySet.vpnGatewayId')
        assert indexes == [5, 6, 7, 8, 9, 10]
        known_error('TINA-6757', 'Call does not support wildcard in key value of tag:key')
