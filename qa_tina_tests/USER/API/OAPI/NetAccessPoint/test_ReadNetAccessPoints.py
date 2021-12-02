import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from specs import check_oapi_error
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.wait_tools import wait_vpc_endpoints_state

NUM_NET_AP = 4
SERVICE_NAMES = ['api', 'oos']

class Test_ReadNetAccessPoints(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.net_ids = []
        cls.route_table_ids = []
        cls.net_ap_ids = []
        super(Test_ReadNetAccessPoints, cls).setup_class()
        try:
            for i in range(NUM_NET_AP):
                net_id = cls.a1_r1.oapi.CreateNet(IpRange='10.0.0.0/16').response.Net.NetId
                cls.net_ids.append(net_id)
                route_table_id = cls.a1_r1.oapi.CreateRouteTable(NetId=net_id).response.RouteTable.RouteTableId
                cls.route_table_ids.append(route_table_id)
                cls.net_ap_ids.append(cls.a1_r1.oapi.CreateNetAccessPoint(
                    NetId=net_id, ServiceName='com.outscale.{}.{}'.format(cls.a1_r1.config.region.name, SERVICE_NAMES[i % 2]),
                    RouteTableIds=[route_table_id]).response.NetAccessPoint.NetAccessPointId)
            wait_vpc_endpoints_state(cls.a1_r1, cls.net_ap_ids, 'available')
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.net_ap_ids[0]], Tags=[{'Key': 'foo', 'Value': 'bar'}])
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            for net_ap_id in cls.net_ap_ids:
                cls.a1_r1.oapi.DeleteNetAccessPoint(NetAccessPointId=net_ap_id)
            for route_table_id in cls.route_table_ids:
                cls.a1_r1.oapi.DeleteRouteTable(RouteTableId=route_table_id)
            for net_id in cls.net_ids:
                cls.a1_r1.oapi.DeleteNet(NetId=net_id)
        finally:
            super(Test_ReadNetAccessPoints, cls).teardown_class()

    def test_T3337_empty_filters(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints()
        assert len(ret.response.NetAccessPoints) == NUM_NET_AP

    def test_T3728_filter_net_id(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'NetIds': [self.net_ids[0]]})
        assert len(ret.response.NetAccessPoints) == 1
        assert ret.response.NetAccessPoints[0].NetId == self.net_ids[0]
        assert ret.response.NetAccessPoints[0].ServiceName == 'com.outscale.{}.{}'.format(self.a1_r1.config.region.name, SERVICE_NAMES[0])
        assert self.route_table_ids[0] in ret.response.NetAccessPoints[0].RouteTableIds

    def test_T3729_filter_net_ap_id(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'NetAccessPointIds': [self.net_ap_ids[0]]})
        assert len(ret.response.NetAccessPoints) == 1
        assert ret.response.NetAccessPoints[0].NetId == self.net_ids[0]
        assert ret.response.NetAccessPoints[0].ServiceName == 'com.outscale.{}.{}'.format(self.a1_r1.config.region.name, SERVICE_NAMES[0])
        assert self.route_table_ids[0] in ret.response.NetAccessPoints[0].RouteTableIds
        assert len(ret.response.NetAccessPoints[0].Tags) == 1

    def test_T3730_filter_multiple_net_ids(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'NetIds': self.net_ids})
        assert len(ret.response.NetAccessPoints) == NUM_NET_AP

    def test_T3731_filter_multiple_net_ap_ids(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'NetAccessPointIds': self.net_ap_ids})
        assert len(ret.response.NetAccessPoints) == NUM_NET_AP

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
            check_oapi_error(error, 3001)

    def test_T3736_filter_net_ids_with_invalid_type(self):
        try:
            ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'NetIds': [True]})
            assert not ret.response.NetAccessPoint
        except OscApiException as error:
            check_oapi_error(error, 4110)

    def test_T3807_filter_servicenames(self):
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'ServiceNames': ['com.outscale.{}.oos'.format(self.a1_r1.config.region.name)]})
        assert len(ret.response.NetAccessPoints) == 2

    def test_T3808_filter_states(self):
        wait_vpc_endpoints_state(self.a1_r1, self.net_ap_ids, state='available')
        ret = self.a1_r1.oapi.ReadNetAccessPoints(Filters={'States': ['available']})
        assert len(ret.response.NetAccessPoints) == NUM_NET_AP

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

    def test_T5974_with_tag_filter(self):
        indexes, _ = misc.execute_tag_tests(self.a1_r1, 'NetAccessPoint', self.net_ap_ids,
                               'oapi.ReadNetAccessPoints', 'NetAccessPoints.NetAccessPointId')
        assert indexes == [3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 19, 20, 24, 25, 26, 27, 28, 29]
        known_error('API-399', 'Read calls do not support wildcards in tag filtering')
