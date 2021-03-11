# -*- coding: utf-8 -*-

import pytest

from qa_tina_tests.USER.FUNCTIONAL.FCU.VPN_Connections.vpn import Vpn


options = [ "aes128-sha256-modp1024!",
            "aes128-sha1-modp2048!",
            "aes128-sha256-modp2048!",
            "aes256-sha256-modp1024!",
            "aes256-sha256-modp2048!",
            "aes256-sha256-modp4096!"]

@pytest.mark.region_internet
class Test_vpn_options(Vpn):
    def test_T5427_vpn_static_strongswan_v1_multi_options(self):
        self.exec_test_vpn(static=True, racoon=False, default_rtb=True, options=options, ike="ikev1")

    def test_T5428_vpn_static_strongswan_v2_multi_options(self):
        self.exec_test_vpn(static=True, racoon=False, default_rtb=True, options=options, ike="ikev2")
