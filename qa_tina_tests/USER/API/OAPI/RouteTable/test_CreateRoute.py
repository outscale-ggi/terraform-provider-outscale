# -*- coding:utf-8 -*-
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_tina_tools.tools.tina.info_keys import ROUTE_TABLE_ID, INTERNET_GATEWAY_ID
from qa_tina_tests.USER.API.OAPI.RouteTable.RouteTable import validate_route_table


class Test_CreateRoute(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateRoute, cls).setup_class()
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
            super(Test_CreateRoute, cls).teardown_class()

    def test_T2015_without_param(self):
        try:
            self.a1_r1.oapi.CreateRoute()
            assert False, 'Call should not have been successful, missing parameter'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2016_with_invalid_params(self):
        try:
            self.a1_r1.oapi.CreateRoute(DestinationIpRange='192.168.0.0/25', RouteTableId=self.vpc_info[ROUTE_TABLE_ID], GatewayId='igw-12345678')
            assert False, 'Call should not have been successful, invalid gateway id'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5001')

    def test_T2017_with_valid_params(self):
        ret = self.a1_r1.oapi.CreateRoute(DestinationIpRange='100.0.0.0/24',
                                          RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                          GatewayId=self.vpc_info[INTERNET_GATEWAY_ID]).response.RouteTable
        validate_route_table(ret, routes=[('gtw', [self.vpc_info[INTERNET_GATEWAY_ID]])])
