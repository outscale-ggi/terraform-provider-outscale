
from qa_tina_tests.USER.FUNCTIONAL.FCU.VPN_Connections.vpn import Vpn


class Test_check_default_conf(Vpn):

    def test_T6117_check_strongswan_conf(self):
        self.exec_test_vpn(static=True, racoon=False, default_rtb=True, check_conf=True)
