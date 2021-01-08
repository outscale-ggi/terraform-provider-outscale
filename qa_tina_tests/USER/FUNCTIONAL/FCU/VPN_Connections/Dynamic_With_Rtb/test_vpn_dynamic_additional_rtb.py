# -*- coding: utf-8 -*-

import pytest

from qa_tina_tests.USER.FUNCTIONAL.FCU.VPN_Connections.vpn import Vpn


@pytest.mark.region_internet
class Test_vpn_dynamic_additional_rtb(Vpn):

    def test_T1851_test_vpn_dynamic_additional_rtb(self):
        self.exec_test_vpn(static=False, racoon= True, default_rtb=False)

    def test_T5142_test_vpn_dynamic_additional_rtb_strongswan(self):
        self.exec_test_vpn(static=False, racoon= False, default_rtb=False)
