# -*- coding: utf-8 -*-

import pytest
from qa_tina_tests.USER.FUNCTIONAL.FCU.VPN_Connections.vpn import Vpn


@pytest.mark.region_internet
class Test_vpn_dynamic(Vpn):

    @pytest.mark.tag_redwire
    def test_T126_test_vpn_dynamic(self):
        self.exec_test_vpn(static=False, default_rtb=True)
