import pytest
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import ROUTE_TABLE_ID, VPC_ID
from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_tina_tools.tools.tina.wait_tools import wait_vpn_gateways_state
from qa_tina_tests.USER.API.OAPI.RouteTable.RouteTable import validate_route_table
from qa_sdk_common.exceptions.osc_exceptions import OscApiException


class Test_UpdateRoutePropagation(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        cls.vgw_id = None
        cls.ret_link = None
        super(Test_UpdateRoutePropagation, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1)
            cls.vgw_id = cls.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
            wait_vpn_gateways_state(cls.a1_r1, [cls.vgw_id], state='available')
            cls.ret_link = cls.a1_r1.oapi.LinkVirtualGateway(VirtualGatewayId=cls.vgw_id, NetId=cls.vpc_info[VPC_ID])
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret_link:
                try:
                    cls.a1_r1.oapi.UnlinkVirtualGateway(VirtualGatewayId=cls.vgw_id, NetId=cls.vpc_info[VPC_ID])
                    wait_vpn_gateways_state(cls.a1_r1, [cls.vgw_id], state='available')
                except:
                    pass
            if cls.vgw_id:
                try:
                    cls.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=cls.vgw_id)
                except:
                    pass
            if cls.vpc_info:
                try:
                    delete_vpc(cls.a1_r1, cls.vpc_info)
                except:
                    pass
        finally:
            super(Test_UpdateRoutePropagation, cls).teardown_class()

    def test_T2377_valid_params(self):
        ret = self.a1_r1.oapi.UpdateRoutePropagation(RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                                     VirtualGatewayId=self.vgw_id, Enable=True).response.RouteTable
        validate_route_table(ret, route_propagating=[self.vgw_id])

    def test_T2378_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.UpdateRoutePropagation(RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                                     VirtualGatewayId=self.vgw_id, Enable=True, DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3559_other_account(self):
        try:
            self.a2_r1.oapi.UpdateRoutePropagation(RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                                   VirtualGatewayId=self.vgw_id, Enable=True).response.RouteTable
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5046')
