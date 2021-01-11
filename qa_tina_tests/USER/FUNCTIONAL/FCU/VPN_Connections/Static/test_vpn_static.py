# -*- coding: utf-8 -*-

import pytest

from qa_tina_tests.USER.FUNCTIONAL.FCU.VPN_Connections.vpn import Vpn


@pytest.mark.region_internet
class Test_vpn_static(Vpn):

    @pytest.mark.tag_redwire
    def test_T125_test_vpn_static(self):
        self.exec_test_vpn(static=True, racoon=True, default_rtb=True)

    def test_T5140_test_vpn_static_strongswan(self):
        self.exec_test_vpn(static=True, racoon=False, default_rtb=True)
