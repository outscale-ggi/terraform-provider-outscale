

def validate_client_gateway(vpn, **kwargs):
    expected_cg = kwargs.get('expected_cg')
    if expected_cg:
        for key, value in expected_cg.items():
            assert getattr(vpn, key) == value, (
                'In ClientGateway, {} is different of expected value {} for key {}'
                .format(getattr(vpn, key), value, key))
    assert vpn.ClientGatewayId.startswith('cgw-')
