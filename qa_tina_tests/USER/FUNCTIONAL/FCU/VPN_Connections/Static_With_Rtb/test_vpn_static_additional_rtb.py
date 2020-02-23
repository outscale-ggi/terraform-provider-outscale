# -*- coding: utf-8 -*-

import pytest
from qa_tina_tests.USER.FUNCTIONAL.FCU.VPN_Connections.vpn import Vpn


@pytest.mark.region_internet
class Test_vpn_static_additional_rtb(Vpn):

    def test_T1850_test_vpn_static_additional_rtb(self):
        self.exec_test_vpn(static=True, default_rtb=False)
