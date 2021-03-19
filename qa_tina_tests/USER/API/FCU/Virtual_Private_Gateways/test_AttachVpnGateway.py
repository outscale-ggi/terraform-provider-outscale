from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_tina_tools.tools.tina.wait_tools import wait_vpn_gateways_attachment_state, wait_vpn_gateways_state


class Test_AttachVpnGateway(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_AttachVpnGateway, cls).setup_class()
        cls.vpc_infos = None
        cls.vgw_id1 = None
        cls.vgw_id2 = None
        cls.atach_status = False
        try:
            cls.vgw_id1 = cls.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1').response.vpnGateway.vpnGatewayId
            cls.vgw_id2 = cls.a2_r1.fcu.CreateVpnGateway(Type='ipsec.1').response.vpnGateway.vpnGatewayId
            cls.vpc_infos = create_vpc(osc_sdk=cls.a1_r1)
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vgw_id1:
                if cls.atach_status:
                    cls.a1_r1.fcu.DetachVpnGateway(VpcId=cls.vpc_infos[VPC_ID], VpnGatewayId=cls.vgw_id1)
                    wait_vpn_gateways_attachment_state(cls.a1_r1, [cls.vgw_id1], 'detached')
                    cls.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=cls.vgw_id1)
                    wait_vpn_gateways_state(cls.a1_r1, [cls.vgw_id1], state='deleted')
            if cls.vgw_id2:
                cls.a2_r1.fcu.DeleteVpnGateway(VpnGatewayId=cls.vgw_id2)
                wait_vpn_gateways_state(cls.a2_r1, [cls.vgw_id2], state='deleted')
            if cls.vpc_infos:
                cleanup_vpcs(cls.a1_r1, cls.vpc_infos[VPC_ID])
        finally:
            super(Test_AttachVpnGateway, cls).teardown_class()

    def test_T4374_without_params(self):
        try:
            self.a1_r1.fcu.AttachVpnGateway()
            assert False, "call should not have been successful, bad number of parameter"
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: VpcID')

    def test_T4375_with_params(self):
        ret = self.a1_r1.fcu.AttachVpnGateway(VpcId=self.vpc_infos[VPC_ID], VpnGatewayId=self.vgw_id1)
        wait_vpn_gateways_attachment_state(self.a1_r1, [self.vgw_id1], 'attached')
        self.atach_status = True
        assert ret.response.attachment.state in ['attaching', 'attached']
        assert ret.response.attachment.vpcId

    def test_T4376_with_vpngateway_of_other_account(self):
        try:
            self.a1_r1.fcu.AttachVpnGateway(VpcId=self.vpc_infos[VPC_ID], VpnGatewayId=self.vgw_id2)
            assert False, "call should not have been successful, bad number of parameter"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpnGatewayID.NotFound',
                         "The VpnGatewayId '{}' does not exist".format(self.vgw_id2))

    def test_T4387_with_other_account_and_vpngateway_of_this_account(self):
        try:
            self.a2_r1.fcu.AttachVpnGateway(VpcId=self.vpc_infos[VPC_ID], VpnGatewayId=self.vgw_id2)
            assert False, "call should not have been successful, bad number of parameter"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpcID.NotFound',
                         "The vpc ID '{}' does not exist".format(self.vpc_infos[VPC_ID]))
