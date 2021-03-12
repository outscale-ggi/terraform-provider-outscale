import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_dry_run
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.test_base import OscTestSuite


class Test_DeleteNetAccessPoint(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteNetAccessPoint, cls).setup_class()
        cls.net_id = None
        cls.route_table_id = None
        cls.net_ap_id = None
        try:
            cls.net_id = cls.a1_r1.oapi.CreateNet(IpRange='10.0.0.0/16').response.Net.NetId
            cls.route_table_id = cls.a1_r1.oapi.CreateRouteTable(NetId=cls.net_id).response.RouteTable.RouteTableId
            cls.net_ap_id = cls.a1_r1.oapi.CreateNetAccessPoint(NetId=cls.net_id,
                                                                ServiceName='com.outscale.{}.api'.format(cls.a1_r1.config.region.name),
                                                                RouteTableIds=[cls.route_table_id]).response.NetAccessPoint.NetAccessPointId
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.net_ap_id:
                cls.a1_r1.oapi.DeleteNetAccessPoint(NetAccessPointId=cls.net_ap_id)
            if cls.route_table_id:
                cls.a1_r1.oapi.DeleteRouteTable(RouteTableId=cls.route_table_id)
            if cls.net_id:
                cls.a1_r1.oapi.DeleteNet(NetId=cls.net_id)
        finally:
            super(Test_DeleteNetAccessPoint, cls).teardown_class()

    def test_T3333_missing_parameter(self):
        try:
            self.a1_r1.oapi.DeleteNetAccessPoint()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T3334_invalid_net_access_point_id(self):
        try:
            self.a1_r1.oapi.DeleteNetAccessPoint(NetAccessPointId='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')
        try:
            self.a1_r1.oapi.DeleteNetAccessPoint(NetAccessPointId='vpce-1234567')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')
        try:
            self.a1_r1.oapi.DeleteNetAccessPoint(NetAccessPointId='vpce-123456789')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')

    def test_T3335_unknown_net_access_point_id(self):
        try:
            self.a1_r1.oapi.DeleteNetAccessPoint(NetAccessPointId='vpce-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5034')

    @pytest.mark.tag_sec_confidentiality
    def test_T3719_other_user(self):
        try:
            self.a2_r1.oapi.DeleteNetAccessPoint(NetAccessPointId=self.net_ap_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5034')

    def test_T3720_valid_params(self):
        self.a1_r1.oapi.DeleteNetAccessPoint(NetAccessPointId=self.net_ap_id)

    def test_T3721_valid_dry_run(self):
        ret = self.a1_r1.oapi.DeleteNetAccessPoint(NetAccessPointId=self.net_ap_id, DryRun=True)
        assert_dry_run(ret)
