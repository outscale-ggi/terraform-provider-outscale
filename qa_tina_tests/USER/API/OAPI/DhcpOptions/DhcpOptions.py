

def validate_dhcp_options(dhcp, **kwargs):
    """
    :param dhcp:
    :param kwargs:
        expected_dhcp
    """
    expected_dhcp = kwargs.get('expected_dhcp')
    if expected_dhcp:
        for key, value in expected_dhcp.items():
            assert getattr(dhcp, key) == value, (
                'In Dhcp, {} is different of expected value {} for key {}'
                .format(getattr(dhcp, key), value, key))
    assert dhcp.DhcpOptionsSetId.startswith('dopt-')
