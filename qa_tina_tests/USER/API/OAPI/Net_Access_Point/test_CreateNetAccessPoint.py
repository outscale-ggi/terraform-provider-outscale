from qa_common_tools.test_base import OscTestSuite
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import assert_dry_run
from qa_common_tools.misc import assert_oapi_error


class Test_CreateNetAccessPoint(OscTestSuite):

    def test_T3329_missing_parameter(self):
        try:
            self.a1_r1.oapi.CreateNetAccessPoint()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateNetAccessPoint(NetId='vpc-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateNetAccessPoint(ServiceName='myservice')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T3330_invalid_net_id(self):
        try:
            self.a1_r1.oapi.CreateNetAccessPoint(NetId='tata', ServiceName='myservice')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')
        try:
            self.a1_r1.oapi.CreateNetAccessPoint(NetId='vpc-1234567', ServiceName='myservice')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')
        try:
            self.a1_r1.oapi.CreateNetAccessPoint(NetId='vpc-123456789', ServiceName='myservice')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')

    def test_T3331_unknown_service_name(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange='10.0.0.0/16').response.Net.NetId
            self.a1_r1.oapi.CreateNetAccessPoint(NetId=net_id, ServiceName='unknown_service')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5040')
        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T3332_invalid_route_table_ids(self):
        net_id = self.a1_r1.oapi.CreateNet(IpRange='10.0.0.0/16').response.Net.NetId
        try:
            self.a1_r1.oapi.CreateNetAccessPoint(NetId=net_id, ServiceName='myservice', RouteTableIds=['tata'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')
        try:
            self.a1_r1.oapi.CreateNetAccessPoint(NetId=net_id, ServiceName='myservice', RouteTableIds=['rtb-1234567'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')
        if net_id:
            self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T3699_valid_params(self):
        net_id = self.a1_r1.oapi.CreateNet(IpRange='10.0.0.0/16').response.Net.NetId
        route_table_id = self.a1_r1.oapi.CreateRouteTable(NetId=net_id).response.RouteTable.RouteTableId
        net_access_point_id = None
        try:
            net_access_point_id = self.a1_r1.oapi.CreateNetAccessPoint(
                NetId=net_id,
                ServiceName='com.outscale.{}.osu'.format(self.a1_r1.config.region.name),
                RouteTableIds=[route_table_id]).response.NetAccessPoint.NetAccessPointId
        finally:
            if net_access_point_id:
                self.a1_r1.oapi.DeleteNetAccessPoint(NetAccessPointId=net_access_point_id)
            if route_table_id:
                self.a1_r1.oapi.DeleteRouteTable(RouteTableId=route_table_id)
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T3700_dry_run(self):
        ret = self.a1_r1.oapi.CreateNetAccessPoint(
            NetId='vpc-12345795688',
            ServiceName='com.outscale.{}.osu'.format(self.a1_r1.config.region.name),
            RouteTableIds=['rtb-titi'],
            DryRun=True)
        assert_dry_run(ret)
