from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_dry_run
from qa_tina_tools.test_base import OscTinaTest
from specs import check_oapi_error


class Test_CreateNetAccessPoint(OscTinaTest):

    def test_T3329_missing_parameter(self):
        try:
            self.a1_r1.oapi.CreateNetAccessPoint()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateNetAccessPoint(NetId='vpc-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateNetAccessPoint(ServiceName='myservice')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T3330_invalid_net_id(self):
        try:
            self.a1_r1.oapi.CreateNetAccessPoint(NetId='tata', ServiceName='myservice')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='tata', prefixes='vpc-')
        try:
            self.a1_r1.oapi.CreateNetAccessPoint(NetId='vpc-1234567', ServiceName='myservice')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='vpc-1234567')
        try:
            self.a1_r1.oapi.CreateNetAccessPoint(NetId='vpc-123456789', ServiceName='myservice')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='vpc-123456789')

    def test_T3331_unknown_service_name(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange='10.0.0.0/16').response.Net.NetId
            self.a1_r1.oapi.CreateNetAccessPoint(NetId=net_id, ServiceName='unknown_service')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5040)
        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T3332_invalid_route_table_ids(self):
        net_id = self.a1_r1.oapi.CreateNet(IpRange='10.0.0.0/16').response.Net.NetId
        try:
            self.a1_r1.oapi.CreateNetAccessPoint(NetId=net_id, ServiceName='myservice', RouteTableIds=['tata'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='tata', prefixes='rtb-')
        try:
            self.a1_r1.oapi.CreateNetAccessPoint(NetId=net_id, ServiceName='myservice', RouteTableIds=['rtb-1234567'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='rtb-1234567')
        if net_id:
            self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T3699_valid_params(self):
        net_id = self.a1_r1.oapi.CreateNet(IpRange='10.0.0.0/16').response.Net.NetId
        route_table_id = self.a1_r1.oapi.CreateRouteTable(NetId=net_id).response.RouteTable.RouteTableId
        net_access_point_ids = []
        services = ['fcu', 'lbu', 'eim', 'icu', 'directlink', 'api', 'kms']
        try:
            for service in services:
                ret = self.a1_r1.oapi.CreateNetAccessPoint(
                    NetId=net_id,
                    ServiceName='com.outscale.{}.{}'.format(self.a1_r1.config.region.name, service),
                    RouteTableIds=[route_table_id])
                assert ret.response.NetAccessPoint.NetAccessPointId
                assert ret.response.NetAccessPoint.NetId
                assert ret.response.NetAccessPoint.RouteTableIds
                assert (ret.response.NetAccessPoint.ServiceName).endswith(service)
                assert ret.response.NetAccessPoint.State
                assert hasattr(ret.response.NetAccessPoint, 'Tags')
                net_access_point_ids.append(ret.response.NetAccessPoint.NetAccessPointId)
        finally:
            if net_access_point_ids:
                for net_access_point_id in net_access_point_ids:
                    self.a1_r1.oapi.DeleteNetAccessPoint(NetAccessPointId=net_access_point_id)
            if route_table_id:
                self.a1_r1.oapi.DeleteRouteTable(RouteTableId=route_table_id)
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T3700_dry_run(self):
        ret = self.a1_r1.oapi.CreateNetAccessPoint(
            NetId='vpc-12345795688',
            ServiceName='com.outscale.{}.api'.format(self.a1_r1.config.region.name),
            RouteTableIds=['rtb-titi'],
            DryRun=True)
        assert_dry_run(ret)
