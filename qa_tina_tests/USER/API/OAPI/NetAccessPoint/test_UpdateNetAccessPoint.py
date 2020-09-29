from qa_test_tools.test_base import OscTestSuite
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error


class Test_UpdateNetAccessPoint(OscTestSuite):

    def test_T3338_missing_parameter(self):
        try:
            self.a1_r1.oapi.UpdateNetAccessPoint()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T3339_invalid_net_access_point_id(self):
        try:
            self.a1_r1.oapi.UpdateNetAccessPoint(NetAccessPointId='tata', AddRouteTableIds=['rtb-12345678'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')
        try:
            self.a1_r1.oapi.UpdateNetAccessPoint(NetAccessPointId='vpce-1234567', AddRouteTableIds=['rtb-12345678'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')
        try:
            self.a1_r1.oapi.UpdateNetAccessPoint(NetAccessPointId='vpce-123456789', AddRouteTableIds=['rtb-12345678'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')

    def test_T3340_unknown_net_access_point_id(self):
        net_id = None
        rtb_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange='10.0.0.0/16').response.Net.NetId
            rtb_id = self.a1_r1.oapi.CreateRouteTable(NetId=net_id).response.RouteTable.RouteTableId
            self.a1_r1.oapi.UpdateNetAccessPoint(NetAccessPointId='vpce-12345678', AddRouteTableIds=[rtb_id])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5034')
        finally:
            if rtb_id:
                self.a1_r1.oapi.DeleteRouteTable(RouteTableId=rtb_id)
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)
