import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_vpc_endpoints_state


class Test_ReadNetAccessPoints(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadNetAccessPoints, cls).setup_class()
        cls.net_id = None
        cls.route_table_id = None
        cls.net_ap_id = None
        cls.service_name1 = 'com.outscale.{}.api'.format(cls.a1_r1.config.region.name)
        cls.service_name2 = 'com.outscale.{}.kms'.format(cls.a1_r1.config.region.name)
        try:
            cls.net_id = cls.a1_r1.oapi.CreateNet(IpRange='10.0.0.0/16').response.Net.NetId
            cls.net_id2 = cls.a1_r1.oapi.CreateNet(IpRange='10.0.0.0/16').response.Net.NetId
            cls.route_table_id = cls.a1_r1.oapi.CreateRouteTable(NetId=cls.net_id).response.RouteTable.RouteTableId
            cls.route_table_id2 = cls.a1_r1.oapi.CreateRouteTable(NetId=cls.net_id2).response.RouteTable.RouteTableId
            cls.net_ap_id = cls.a1_r1.oapi.CreateNetAccessPoint(NetId=cls.net_id, ServiceName=cls.service_name1,
                                                                RouteTableIds=[cls.route_table_id]).response.NetAccessPoint.NetAccessPointId
            cls.net_ap_id2 = cls.a1_r1.oapi.CreateNetAccessPoint(NetId=cls.net_id2, ServiceName=cls.service_name2,
                                                                 RouteTableIds=[cls.route_table_id2]).response.NetAccessPoint.NetAccessPointId
            wait_vpc_endpoints_state(cls.a1_r1, [cls.net_ap_id, cls.net_ap_id2], 'available')
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.net_ap_id], Tags=[{'Key': 'foo', 'Value': 'bar'}])
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.net_ap_id:
                cls.a1_r1.oapi.DeleteNetAccessPoint(NetAccessPointId=cls.net_ap_id)
            if cls.net_ap_id2:
                cls.a1_r1.oapi.DeleteNetAccessPoint(NetAccessPointId=cls.net_ap_id2)
            if cls.route_table_id:
                cls.a1_r1.oapi.DeleteRouteTable(RouteTableId=cls.route_table_id)
            if cls.route_table_id2:
                cls.a1_r1.oapi.DeleteRouteTable(RouteTableId=cls.route_table_id2)
            if cls.net_id:
                cls.a1_r1.oapi.DeleteNet(NetId=cls.net_id)
            if cls.net_id2:
                cls.a1_r1.oapi.DeleteNet(NetId=cls.net_id2)
        finally:
            super(Test_ReadNetAccessPoints, cls).teardown_class()

    def test_T3337_empty_filters(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints()
        assert len(ret.response.NetAccessPoints) == 2

    def test_T3728_filter_net_id(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'NetIds': [self.net_id]})
        assert len(ret.response.NetAccessPoints) == 1
        assert ret.response.NetAccessPoints[0].NetId == self.net_id
        assert ret.response.NetAccessPoints[0].ServiceName == self.service_name1
        assert self.route_table_id in ret.response.NetAccessPoints[0].RouteTableIds

    def test_T3729_filter_net_ap_id(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'NetAccessPointIds': [self.net_ap_id]})
        assert len(ret.response.NetAccessPoints) == 1
        assert ret.response.NetAccessPoints[0].NetId == self.net_id
        assert ret.response.NetAccessPoints[0].ServiceName == self.service_name1
        assert self.route_table_id in ret.response.NetAccessPoints[0].RouteTableIds
        assert len(ret.response.NetAccessPoints[0].Tags) == 1

    def test_T3730_filter_multiple_net_ids(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'NetIds': [self.net_id, self.net_id2]})
        assert len(ret.response.NetAccessPoints) == 2

    def test_T3731_filter_multiple_net_ap_ids(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'NetAccessPointIds': [self.net_ap_id, self.net_ap_id2]})
        assert len(ret.response.NetAccessPoints) == 2

    @pytest.mark.tag_sec_confidentiality
    def test_T3732_empty_filters_other_user(self):
        ret = self.a2_r1.oapi.ReadNetAccessPoints()
        assert not ret.response.NetAccessPoints

    def test_T3733_inexistent_filter_net_ap_id(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'NetAccessPointIds': ['vpc-111111111']})
        assert not ret.response.NetAccessPoints

    def test_T3734_inexistent_filter_net_id(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'NetIds': ['vpce-111111111']})
        assert not ret.response.NetAccessPoints

    def test_T3735_inalid_filter(self):
        try:
            ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'titi': ['titi']})
            assert not ret.response.NetAccessPoints
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T3736_filter_net_ids_with_invalid_type(self):
        try:
            ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'NetIds': [True]})
            assert not ret.response.NetAccessPoint
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T3807_filter_servicenames(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'ServiceNames': ['com.outscale.in-west-2.kms']})
        assert len(ret.response.NetAccessPoints) == 1

    def test_T3808_filter_states(self):
        wait_vpc_endpoints_state(self.a1_r1, [self.net_ap_id, self.net_ap_id2], state='available')
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'States': ['available']})
        assert len(ret.response.NetAccessPoints) == 2

    def test_T3809_invalid_filter_servicenames(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'ServiceNames': ['tititoto']})
        assert len(ret.response.NetAccessPoints) == 0

    def test_T3810_invalid_filter_states(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'States': ['tititoto']})
        assert len(ret.response.NetAccessPoints) == 0

    def test_T4423_with_tagkeys_filter(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'TagKeys': ['foo']})
        assert len(ret.response.NetAccessPoints) == 1
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'TagKeys': ['foo1']})
        assert len(ret.response.NetAccessPoints) == 0

    def test_T4424_with_tagvalues_filter(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'TagValues': ['bar']})
        assert len(ret.response.NetAccessPoints) == 1
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'TagValues': ['bar1']})
        assert len(ret.response.NetAccessPoints) == 0

    def test_T4425_with_tags_filter(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'Tags': ['foo=bar']})
        assert len(ret.response.NetAccessPoints) == 1
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'Tags': ['foo1=bar1']})
        assert len(ret.response.NetAccessPoints) == 0
