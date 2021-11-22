# -*- coding: utf-8 -*-

import ipaddress
import pytest

from qa_tina_tests.USER.FUNCTIONAL.FCU.VPN_Connections.vpn import Vpn
from qa_test_tools.misc import id_generator


@pytest.mark.region_internet
class Test_update_vpn_connection(Vpn):

    def test_T6103_with_presharedkey(self):
        presharedkey = id_generator(size=64)
        self.exec_test_vpn(static=False, racoon=False, default_rtb=True, presharedkey=presharedkey)

    def test_T6115_with_tunnelinsideiprange(self):
        self.exec_test_vpn(static=False, racoon=False, default_rtb=True, tunnelinsideiprange=ipaddress.ip_address("169.254.254.8"))

    def test_T6116_with_presharedkey_and_tunnelinsideiprange(self):
        presharedkey = id_generator(size=64)
        self.exec_test_vpn(static=False, racoon=False, default_rtb=True, presharedkey=presharedkey,
                           tunnelinsideiprange=ipaddress.ip_address("169.254.254.8"))
