
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import ROUTE_TABLE_ID, INTERNET_GATEWAY_ID
from specs import check_oapi_error


class Test_UpdateRoute(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateRoute, cls).setup_class()
        cls.vpc_info = None
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, nb_subnet=0, igw=True, default_rtb=True)
            cls.cidr_destination = '100.0.0.0/24'
            cls.a1_r1.oapi.CreateRoute(DestinationIpRange=cls.cidr_destination, RouteTableId=cls.vpc_info[ROUTE_TABLE_ID],
                                       GatewayId=cls.vpc_info[INTERNET_GATEWAY_ID],)
        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_UpdateRoute, cls).teardown_class()

    def test_T2026_without_param(self):
        try:
            self.a1_r1.oapi.UpdateRoute()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T2027_with_invalid_params(self):
        try:
            self.a1_r1.oapi.UpdateRoute(DestinationIpRange='100.0.0.0/24', RouteTableId=self.vpc_info[ROUTE_TABLE_ID], VmId="i-12345678")
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5063, id="i-12345678")

    def test_T2941_with_invalid_vm_id_params(self):
        try:
            self.a1_r1.oapi.UpdateRoute(DestinationIpRange='100.0.0.0/24', RouteTableId=self.vpc_info[ROUTE_TABLE_ID], VmId="i-123456")
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='i-123456')

    def test_T2028_with_valid_params(self):
        self.a1_r1.oapi.UpdateRoute(DestinationIpRange='100.0.0.0/24', RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                    GatewayId=self.vpc_info[INTERNET_GATEWAY_ID])

    def test_T3525_dry_run(self):
        ret = self.a1_r1.oapi.UpdateRoute(DestinationIpRange='100.0.0.0/24', RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                          GatewayId=self.vpc_info[INTERNET_GATEWAY_ID], DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3526_other_account(self):
        try:
            self.a2_r1.oapi.UpdateRoute(DestinationIpRange='100.0.0.0/24', RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                        GatewayId=self.vpc_info[INTERNET_GATEWAY_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5046, id=self.vpc_info[ROUTE_TABLE_ID])
