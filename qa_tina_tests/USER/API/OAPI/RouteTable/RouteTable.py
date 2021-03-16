

def validate_route_table(route_table, link=None, route_propagating=None, routes=None):
    """Validate a route table.

    :param dict route_table: The route table to validate.
    :param bool link: Check Link or not.
    :param list route_propagating: This list containing VirtualGatewayId to check.
    :param list routes: List of tuple (resource_type, [id1, id2])
        resource_type expected is ('gtw', 'nat_service', 'net_peering', 'vm', 'nic')
    :return:
    """
    assert hasattr(route_table, 'RouteTableId')
    assert route_table.RouteTableId.startswith('rtb-')
    assert hasattr(route_table, 'NetId')
    assert route_table.NetId.startswith('vpc-')
    assert hasattr(route_table, 'LinkRouteTables')
    if link:
        for link_rt in route_table.LinkRouteTables:
            assert hasattr(route_table, 'LinkRouteTableId')
            assert link_rt.LinkRouteTableId.startswith('rtbassoc-')
            assert hasattr(route_table, 'RouteTableId')
            assert link_rt.RouteTableId.startswith('rtb-')
            assert hasattr(route_table, 'Main')
    assert hasattr(route_table, 'RoutePropagatingVirtualGateways')
    if route_propagating:
        for rpvg in route_table.RoutePropagatingVirtualGateways:
            assert hasattr(rpvg, 'VirtualGatewayId')
            assert rpvg.VirtualGatewayId in route_propagating
    assert hasattr(route_table, 'Tags')
    assert hasattr(route_table, 'Routes')
    for route in route_table.Routes:
        assert hasattr(route, 'CreationMethod')
        assert hasattr(route, 'DestinationIpRange')
        assert hasattr(route, 'State')
        for sub_route in routes or []:
            if sub_route[0] == 'gtw' and hasattr(route, 'GatewayId'):
                assert route.GatewayId in sub_route[1]
            if sub_route[0] == 'nat_service' and hasattr(route, 'NatServiceId'):
                assert route.NatServiceId in sub_route[1]
            if sub_route[0] == 'net_peering' and hasattr(route, 'NetPeeringId'):
                assert route.NetPeeringId in sub_route[1]
            if sub_route[0] == 'vm' and hasattr(route, 'VmId'):
                assert route.VmId in sub_route[1]
            if sub_route[0] == 'nic' and hasattr(route, 'NicId'):
                assert route.NicId in sub_route[1]
