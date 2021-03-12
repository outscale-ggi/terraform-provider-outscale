
import os
import random
import re
import time

from netaddr import IPNetwork, IPAddress
import pytest

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import wait
from qa_tina_tools.tools.tina import wait_tools


@pytest.mark.region_admin
class Test_fw_vgw(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_fw_vgw, cls).setup_class()
        cls.cgw_id = None
        cls.vgw_id = None
        cls.vpn_id = None
        try:
            ret = cls.a1_r1.fcu.CreateCustomerGateway(BgpAsn=65000,
                                                      IpAddress='.'.join(str(i) for i in random.sample(list(range(1, 254)), 4)),
                                                      Type='ipsec.1')
            cls.cgw_id = ret.response.customerGateway.customerGatewayId

            ret = cls.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1')
            cls.vgw_id = ret.response.vpnGateway.vpnGatewayId

            ret = cls.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=cls.cgw_id,
                                                    Type='ipsec.1',
                                                    VpnGatewayId=cls.vgw_id,
                                                    Options={'StaticRoutesOnly': True})
            cls.vpn_id = ret.response.vpnConnection.vpnConnectionId
            wait_tools.wait_vpn_connections_state(cls.a1_r1, [cls.vpn_id], state='available')

            ret = cls.a1_r1.intel.netimpl.firewall.get_firewalls(resource=cls.vgw_id)
            inst_id = ret.response.result.master.vm
            wait_tools.wait_instance_service_state(cls.a1_r1, [inst_id], state='ready')
            ret = cls.a1_r1.intel.nic.find(filters={'vm': inst_id})

            inst_ip = None
            for nic in ret.response.result:
                if IPAddress(nic.ips[0].ip) in IPNetwork(cls.a1_r1.config.region.get_info(constants.FW_ADMIN_SUBNET)):
                    inst_ip = nic.ips[0].ip
            assert inst_ip

            cls.sshclient = SshTools.check_connection_paramiko(inst_ip,
                                                               os.path.expanduser(cls.a1_r1.config.region.get_info(constants.FW_KP)),
                                                               username='root',
                                                               retry=30,
                                                               timeout=10)

        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpn_id:
                cls.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=cls.vpn_id)
                wait.wait_VpnConnections_state(cls.a1_r1, [cls.vpn_id], state='deleted', cleanup=True)
            if cls.vgw_id:
                cls.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=cls.vgw_id)
                wait_tools.wait_vpn_gateways_state(cls.a1_r1, [cls.vgw_id], state='deleted')
            if cls.cgw_id:
                cls.a1_r1.fcu.DeleteCustomerGateway(CustomerGatewayId=cls.cgw_id)
                wait_tools.wait_customer_gateways_state(cls.a1_r1, [cls.cgw_id], state='deleted')
        finally:
            super(Test_fw_vgw, cls).teardown_class()

    def test_T1892_check_agent(self):
        assert SshTools.check_service(self.sshclient, 'osc-agent')

    def test_T1894_check_dns(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "cat /etc/resolv.conf")
        for dns in self.a1_r1.config.region.get_info(constants.FW_DNS_SERVERS):
            pattern = re.compile('nameserver {}'.format(dns))
            assert re.search(pattern, out)

    def test_T1895_check_ntp(self):
        for i in range(30):
            out, _, _ = SshTools.exec_command_paramiko(self.sshclient, 'ntpq -pn')
            if re.search(r'\*({})'.format('|'.join(self.a1_r1.config.region.get_info(constants.FW_NTP_SERVER_PREFIX))), out):
                break
            if i == 30 - 1:
                pytest.fail("NTP sync failed: {}".format(out))
            time.sleep(30)

    def test_T1897_check_consul(self):
        assert SshTools.check_service(self.sshclient, 'consul')

    def test_T1898_check_salt(self):
        assert SshTools.check_service(self.sshclient, 'salt-minion')

    def test_T1899_check_nginx(self):
        pytest.skip('nginx not available anymore')
        assert SshTools.check_service(self.sshclient, 'nginx')

    def test_T1905_check_service(self):
        assert SshTools.check_service(self.sshclient, 'strongswan', pattern_str='.* is running.*')

    def test_T1900_check_zebra(self):
        assert SshTools.check_service(self.sshclient, 'zebra')

    def test_T1901_check_bgpd(self):
        assert SshTools.check_service(self.sshclient, 'bgpd')

    def test_T1902_check_netns(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "ip netns exec {} ifconfig | grep Link".format(self.vgw_id))
        assert re.search('lo', out)
        assert re.search('tun-', out)
        assert re.search('eth0', out)
        assert re.search('eth2', out)
        # TODO: Add tests

    def test_T1903_check_hostname(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "hostname")
        pattern = re.compile('fw-master-{}'.format(self.vgw_id))
        assert re.search(pattern, out)

    def test_T1904_check_kernel(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "uname -a")
        pattern = re.compile(self.a1_r1.config.region.get_info(constants.FW_KERNEL_VERSION))
        assert re.search(pattern, out)

    def test_T1929_check_cpu_generation(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "cat /proc/cpuinfo")
        pattern = re.compile('Sandy Bridge')
        assert re.search(pattern, out)
