from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_tina_tools.tools.tina.wait_tools import wait_vpn_gateways_attachment_state, wait_vpn_gateways_state


class Test_DetachVpnGateway(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_infos = []
        cls.detach_status = True
        cls.vgw_id = None
        cls.res_attach = None
        super(Test_DetachVpnGateway, cls).setup_class()
        try:
            cls.vgw_id = cls.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1').response.vpnGateway.vpnGatewayId
            cls.vpc_infos = create_vpc(osc_sdk=cls.a1_r1)
            cls.res_attach = cls.a1_r1.fcu.AttachVpnGateway(VpcId=cls.vpc_infos[VPC_ID], VpnGatewayId=cls.vgw_id)
            cls.detach_status = False
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    def setup_method(self, method):
        try:
            if self.__class__.detach_status:
                self.res_attach = self.a1_r1.fcu.AttachVpnGateway(VpcId=self.vpc_infos[VPC_ID], VpnGatewayId=self.vgw_id)
                wait_vpn_gateways_attachment_state(self.a1_r1, [self.vgw_id], 'attached')
                self.__class__.detach_status = False
        finally:
            OscTestSuite.setup_method(self, method)

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vgw_id:
                try:
                    if not cls.detach_status:
                        cls.a1_r1.fcu.DetachVpnGateway(VpcId=cls.vpc_infos[VPC_ID], VpnGatewayId=cls.vgw_id)
                    wait_vpn_gateways_attachment_state(cls.a1_r1, [cls.vgw_id], 'detached')
                    wait_vpn_gateways_state(cls.a1_r1, [cls.vgw_id], state='available')
                    cls.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=cls.vgw_id)
                    wait_vpn_gateways_state(cls.a1_r1, [cls.vgw_id], state='deleted')
                except:
                    pass
            if cls.vpc_infos:
                delete_vpc(cls.a1_r1, cls.vpc_infos)
        finally:
            super(Test_DetachVpnGateway, cls).teardown_class()

    def test_T4173_valid_params(self):
        self.a1_r1.fcu.DetachVpnGateway(VpcId=self.vpc_infos[VPC_ID], VpnGatewayId=self.vgw_id)
        wait_vpn_gateways_attachment_state(self.a1_r1, [self.vgw_id], 'detached')
        self.__class__.detach_status = True

    def test_T4174_detach_with_invalid_Vpc_Id(self):
        try:
            self.a1_r1.fcu.DetachVpnGateway(VpcId=self.vpc_infos, VpnGatewayId=self.vgw_id)
            self.__class__.detach_status = True
            assert False, "Remove known error !"
            assert False, "Calls shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterType', None)
