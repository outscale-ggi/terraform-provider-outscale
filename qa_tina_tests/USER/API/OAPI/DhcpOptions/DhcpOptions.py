# -*- coding:utf-8 -*-


def validate_dhcp_options(dhcp, **kwargs):
    """
    :param dhcp: 
    :param kwargs:
        expected_dhcp
    """
    expected_dhcp = kwargs.get('expected_dhcp')
    if expected_dhcp:
        for k, v in expected_dhcp.items():
            assert getattr(dhcp, k) == v, (
                'In Dhcp, {} is different of expected value {} for key {}'
                .format(getattr(dhcp, k), v, k))
    assert dhcp.DhcpOptionsSetId.startswith('dopt-')
