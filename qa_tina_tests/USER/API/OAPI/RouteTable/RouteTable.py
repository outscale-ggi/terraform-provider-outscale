# -*- coding:utf-8 -*-


def validate_route_table(rt, link=None, route_propagating=None, routes=None):
    """Validate a route table.

    :param dict rt: The route table to validate.
    :param bool link: Check Link or not.
    :param list route_propagating: This list containing VirtualGatewayId to check.
    :param list routes: List of tuple (resource_type, [id1, id2])
        resource_type expected is ('gtw', 'nat_service', 'net_peering', 'vm', 'nic')
    :return:
    """
    assert hasattr(rt, 'RouteTableId')
    assert rt.RouteTableId.startswith('rtb-')
    assert hasattr(rt, 'NetId')
    assert rt.NetId.startswith('vpc-')
    assert hasattr(rt, 'LinkRouteTables')
    if link:
        for link_rt in rt.LinkRouteTables:
            assert hasattr(rt, 'LinkRouteTableId')
            assert link_rt.LinkRouteTableId.startswith('rtbassoc-')
            assert hasattr(rt, 'RouteTableId')
            assert link_rt.RouteTableId.startswith('rtb-')
            assert hasattr(rt, 'Main')
    assert hasattr(rt, 'RoutePropagatingVirtualGateways')
    if route_propagating:
        for x in rt.RoutePropagatingVirtualGateways:
            assert hasattr(x, 'VirtualGatewayId')
            assert x.VirtualGatewayId in route_propagating
    assert hasattr(rt, 'Tags')
    assert hasattr(rt, 'Routes')
    for x in rt.Routes:
        assert hasattr(x, 'CreationMethod')
        assert hasattr(x, 'DestinationIpRange')
        assert hasattr(x, 'State')
        for y in routes or []:
            if y[0] == 'gtw' and hasattr(x, 'GatewayId'):
                assert x.GatewayId in y[1]
            if y[0] == 'nat_service' and hasattr(x, 'NatServiceId'):
                assert x.NatServiceId in y[1]
            if y[0] == 'net_peering' and hasattr(x, 'NetPeeringId'):
                assert x.NetPeeringId in y[1]
            if y[0] == 'vm' and hasattr(x, 'VmId'):
                assert x.VmId in y[1]
            if y[0] == 'nic' and hasattr(x, 'NicId'):
                assert x.NicId in y[1]
