# -*- coding:utf-8 -*-
import pytest

from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import ROUTE_TABLE_ID, INTERNET_GATEWAY_ID, VPC_ID, SUBNETS, SUBNET_ID


class Test_ReadRouteTables(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadRouteTables, cls).setup_class()
        cls.vpc_info = None
        cls.rtb2 = None
        cls.rtb2 = None
        cls.ret_create = None
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, nb_subnet=1, igw=True, default_rtb=True)
            cls.cidr_destination = '100.0.0.0/24'
            cls.rtb1 = cls.a1_r1.oapi.CreateRoute(DestinationIpRange=cls.cidr_destination, RouteTableId=cls.vpc_info[ROUTE_TABLE_ID],
                                       GatewayId=cls.vpc_info[INTERNET_GATEWAY_ID])
            cls.rtb2 = cls.a1_r1.oapi.CreateRoute(DestinationIpRange=cls.cidr_destination, RouteTableId=cls.vpc_info[ROUTE_TABLE_ID],
                                       GatewayId=cls.vpc_info[INTERNET_GATEWAY_ID])
            cls.ret_create = cls.a1_r1.fcu.CreateRouteTable(VpcId=cls.vpc_info[VPC_ID])
            cls.link_id = cls.a1_r1.oapi.LinkRouteTable(SubnetId=cls.vpc_info[SUBNETS][0][SUBNET_ID],
                                                        RouteTableId=cls.ret_create.response.routeTable.routeTableId).response.LinkRouteTableId
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    @classmethod
    def teardown_class(cls):
        try:
            if cls.link_id:
                cls.a1_r1.oapi.UnlinkRouteTable(LinkRouteTableId=cls.link_id)
            if cls.ret_create:
                cls.a1_r1.fcu.DeleteRouteTable(RouteTableId=cls.ret_create.response.routeTable.routeTableId)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_ReadRouteTables, cls).teardown_class()

    def test_T2019_without_filters(self):
        res = self.a1_r1.oapi.ReadRouteTables().response
        assert res.RouteTables
        assert len(res.RouteTables[0].LinkRouteTables) != 0
        assert any(rt.NetId == self.vpc_info[VPC_ID] for rt in res.RouteTables)
        assert any(any(getattr(route, 'GatewayId', None) == self.vpc_info[INTERNET_GATEWAY_ID] for route in rt.Routes) for rt in res.RouteTables)

    def test_T2020_bad_filter_combination(self):
        res = self.a1_r1.oapi.ReadRouteTables(Filters={'NetIds': [self.vpc_info['vpc_id']], 'RouteGatewayIds': ['igw-12345']}).response
        assert not res.RouteTables

    def test_T2021_net_ids_filter(self):
        res = self.a1_r1.oapi.ReadRouteTables(Filters={'NetIds': [self.vpc_info[VPC_ID]]}).response
        assert all(rt.NetId == self.vpc_info[VPC_ID] for rt in res.RouteTables)

    def test_T5548_with_link_rtb_ids_filter(self):
        try:
            ret = self.a1_r1.oapi.ReadRouteTables(Filters={'LinkRouteTableLinkRouteTableIds': [self.link_id]})
            assert len(ret.response.RouteTables) >= 1
            assert False, 'Remove known error'
        except AssertionError:
            known_error('GTW-1765', 'LinkRouteTableLinkRouteTableIds filter does not work')

    def test_T2022_route_table_ids_filter(self):
        res = self.a1_r1.oapi.ReadRouteTables(Filters={'RouteTableIds': [self.vpc_info[ROUTE_TABLE_ID]]}).response
        assert all(rt.RouteTableId == self.vpc_info[ROUTE_TABLE_ID] for rt in res.RouteTables)

    def test_T4155_route_table_check_attributes(self):
        routes = self.a1_r1.oapi.ReadRouteTables(Filters={'RouteTableIds': [self.vpc_info[ROUTE_TABLE_ID]]}).response.RouteTables[0].Routes
        for route in routes:
            assert route.CreationMethod
            assert route.DestinationIpRange
            assert route.CreationMethod == 'CreateRouteTable' or route.GatewayId
            assert route.State

    def test_T2023_route_gateway_ids_filter(self):
        res = self.a1_r1.oapi.ReadRouteTables(Filters={'RouteGatewayIds': [self.vpc_info[INTERNET_GATEWAY_ID]]}).response
        assert all(any(getattr(route, 'GatewayId', None) == self.vpc_info[INTERNET_GATEWAY_ID] for route in rt.Routes) for rt in res.RouteTables)

    def test_T2024_route_creation_methods_filter(self):
        res = self.a1_r1.oapi.ReadRouteTables(Filters={'RouteCreationMethods': ['CreateRoute']}).response
        assert all(any(getattr(route, 'CreationMethod', None) == 'CreateRoute' for route in rt.Routes) for rt in res.RouteTables)

    def test_T2025_route_destination_ip_ranges_filter(self):
        res = self.a1_r1.oapi.ReadRouteTables(Filters={'RouteDestinationIpRanges': [self.cidr_destination]}).response
        assert all(any(getattr(route, 'DestinationIpRange', None) == self.cidr_destination for route in rt.Routes) for rt in res.RouteTables)

    @pytest.mark.tag_sec_confidentiality
    def test_T3413_with_other_account(self):
        res = self.a2_r1.oapi.ReadRouteTables().response
        assert not res.RouteTables

    @pytest.mark.tag_sec_confidentiality
    def test_T3414_with_other_account_filters(self):
        res = self.a2_r1.oapi.ReadRouteTables(Filters={'NetIds': [self.vpc_info[VPC_ID]]}).response
        assert not res.RouteTables

    def test_T4149_with_linked_route_table(self):
        self.a1_r1.oapi.LinkRouteTable(RouteTableId=self.vpc_info[ROUTE_TABLE_ID], SubnetId=self.vpc_info['subnets'][0]['subnet_id'])
        ret = self.a1_r1.oapi.ReadRouteTables()
        assert ret.response.RouteTables[0].LinkRouteTables[0].LinkRouteTableId

    def test_T4400_with_route_propagation_enabled(self):
        try:
            vgw_id = self.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
            self.a1_r1.oapi.LinkVirtualGateway(VirtualGatewayId=vgw_id, NetId=self.vpc_info[VPC_ID])
            self.a1_r1.oapi.UpdateRoutePropagation(RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                                   VirtualGatewayId=vgw_id, Enable=True)
            self.a1_r1.oapi.ReadRouteTables()
        finally:
            self.a1_r1.oapi.UpdateRoutePropagation(RouteTableId=self.vpc_info[ROUTE_TABLE_ID],
                                                   VirtualGatewayId=vgw_id, Enable=False)
            self.a1_r1.oapi.UnlinkVirtualGateway(VirtualGatewayId=vgw_id, NetId=self.vpc_info[VPC_ID])
            self.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id)

    def test_T5065_LinkRouteTableIds_filters(self):
        ret = self.a1_r1.oapi.ReadRouteTables(Filters={'LinkRouteTableIds': [self.vpc_info[ROUTE_TABLE_ID]]})
        assert len(ret.response.RouteTables) == 1
        assert ret.response.RouteTables[0].RouteTableId == self.vpc_info[ROUTE_TABLE_ID]

    def test_T5066_LinkRouteTableMain_filters(self):
        ret = self.a1_r1.oapi.ReadRouteTables(Filters={'LinkRouteTableMain': False})
        assert len(ret.response.RouteTables) == 1
        assert ret.response.RouteTables[0].RouteTableId == self.ret_create.response.routeTable.routeTableId
        ret = self.a1_r1.oapi.ReadRouteTables(Filters={'LinkRouteTableMain': True})
        assert len(ret.response.RouteTables) == 1
        assert ret.response.RouteTables[0].RouteTableId == self.vpc_info[ROUTE_TABLE_ID]
