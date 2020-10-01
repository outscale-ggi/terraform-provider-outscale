def validate_client_gateway(vpn, **kwargs):
    expected_cg = kwargs.get('expected_cg')
    if expected_cg:
        for k, v in expected_cg.items():
            assert getattr(vpn, k) == v, (
                'In ClientGateway, {} is different of expected value {} for key {}'
                .format(getattr(vpn, k), v, k))
    assert vpn.ClientGatewayId.startswith('cgw-')
