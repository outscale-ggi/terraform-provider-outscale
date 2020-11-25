# -*- coding:utf-8 -*-
import pytest

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import ROUTE_TABLE_ID, INTERNET_GATEWAY_ID
from qa_tina_tests.USER.API.OAPI.RouteTable.RouteTable import validate_route_table
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run


class Test_DeleteRoute(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteRoute, cls).setup_class()
        cls.vpc_info = None
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, nb_subnet=0, igw=True, default_rtb=True)
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_DeleteRoute, cls).teardown_class()

    def test_T2018_with_valid_params(self):
        self.a1_r1.oapi.CreateRoute(DestinationIpRange='100.0.0.0/24', RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                    GatewayId=self.vpc_info[INTERNET_GATEWAY_ID])
        ret = self.a1_r1.oapi.DeleteRoute(RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                          DestinationIpRange='100.0.0.0/24').response.RouteTable
        validate_route_table(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3508_with_other_user(self):
        try:
            self.a1_r1.oapi.CreateRoute(DestinationIpRange='100.0.0.0/24', RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                        GatewayId=self.vpc_info[INTERNET_GATEWAY_ID])
            self.a2_r1.oapi.DeleteRoute(RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                        DestinationIpRange='100.0.0.0/24')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5046')

    def test_T3509_valid_dry_run(self):
        self.a1_r1.oapi.CreateRoute(DestinationIpRange='100.0.0.0/24', RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                    GatewayId=self.vpc_info[INTERNET_GATEWAY_ID])
        ret = self.a1_r1.oapi.DeleteRoute(RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                          DestinationIpRange='100.0.0.0/24', DryRun=True)
        assert_dry_run(ret)

    def test_T3510_invalid_dry_run(self):
        try:
            self.a1_r1.oapi.CreateRoute(DestinationIpRange='100.0.0.0/24', RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                        GatewayId=self.vpc_info[INTERNET_GATEWAY_ID])
            self.a1_r1.oapi.DeleteRoute(DryRun=True)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
