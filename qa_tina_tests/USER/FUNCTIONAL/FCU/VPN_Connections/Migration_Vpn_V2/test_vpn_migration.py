# -*- coding: utf-8 -*-

import pytest
from qa_tina_tests.USER.FUNCTIONAL.FCU.VPN_Connections.vpn import Vpn


@pytest.mark.region_internet
class Test_vpn_migration(Vpn):

    def test_T5429_vpn_static_strongswan_v1_to_v2(self):
        self.exec_test_vpn(static=True, racoon=False, default_rtb=True, ike="ikev1", migration=True)
