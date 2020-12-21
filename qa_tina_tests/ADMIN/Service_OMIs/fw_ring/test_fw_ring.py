# pylint: disable=missing-docstring
import os
import re
import time
import pytest
from qa_test_tools.test_base import OscTestSuite
from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from netaddr import IPNetwork, IPAddress


class Test_fw_ring(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_fw_ring, cls).setup_class()
        try:
            ret = cls.a1_r1.intel.subnet.find(network='vpc-00000000')
            cls.subnet_id = ret.response.result[1].id
            ret = cls.a1_r1.intel.netimpl.firewall.get_firewalls(resource=cls.subnet_id)
            inst_id = ret.response.result.master.vm
            ret = cls.a1_r1.intel.nic.find(filters={'vm': inst_id})

            inst_ip = None
            for nic in ret.response.result:
                if IPAddress(nic.ips[0].ip) in IPNetwork(cls.a1_r1.config.region.get_info(constants.FW_ADMIN_SUBNET)):
                    inst_ip = nic.ips[0].ip
            assert inst_ip

            cls.sshclient = SshTools.check_connection_paramiko(inst_ip,
                                                               os.path.expanduser(cls.a1_r1.config.region.get_info(constants.FW_KP)),
                                                               username='root')

        except Exception as error:
            cls.teardown_class()
            raise error

    @classmethod
    def teardown_class(cls):
        super(Test_fw_ring, cls).teardown_class()

    def test_T1852_check_agent(self):
        assert SshTools.check_service(self.sshclient, 'osc-agent')

    def test_T1854_check_dns(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "cat /etc/resolv.conf")
        for dns in self.a1_r1.config.region.get_info(constants.FW_DNS_SERVERS):
            pattern = re.compile('nameserver {}'.format(dns))
            assert re.search(pattern, out)

    def test_T1855_check_ntp(self):
        retry = 30
        wait = 30
        for i in range(retry):
            out, _, _ = SshTools.exec_command_paramiko(self.sshclient, 'ntpq -pn')
            if re.search(r'\*({})'.format('|'.join(self.a1_r1.config.region.get_info(constants.FW_NTP_SERVER_PREFIX))), out):
                break
            if i == retry - 1:
                pytest.fail("NTP sync failed: {}".format(out))
            time.sleep(wait)

    def test_T1856_check_zabbix(self):
        assert SshTools.check_service(self.sshclient, 'zabbix-agent', 'zabbix_agent.* is running')

    def test_T1857_check_consul(self):
        assert SshTools.check_service(self.sshclient, 'consul')

    def test_T1858_check_salt(self):
        assert SshTools.check_service(self.sshclient, 'salt-minion')

    def test_T1859_check_nginx(self):
        assert SshTools.check_service(self.sshclient, 'nginx')

    def test_T1860_check_zebra(self):
        pass
        #assert SshTools.check_service(self.sshclient, 'zebra')

    def test_T1861_check_ospfd(self):
        pass
        #assert SshTools.check_service(self.sshclient, 'ospfd')

    def test_T1862_check_network(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "ifconfig")
        assert re.search('eth0', out)
        assert re.search('eth1', out)
        assert re.search('eth1.', out)
        assert re.search('eth2', out)
        assert re.search('eth3', out)
        assert re.search('lo', out)
        # TODO: Add tests

    def test_T1863_check_hostname(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "hostname")
        pattern = re.compile('fw-master-{}'.format(self.subnet_id))
        assert re.search(pattern, out)

    def test_T1864_check_kernel(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "uname -a")
        pattern = re.compile('x86_64 x86_64 x86_64 GNU/Linux')
        assert re.search(pattern, out)

    def test_T1927_check_cpu_generation(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "cat /proc/cpuinfo")
        pattern = re.compile('Sandy Bridge')
        assert re.search(pattern, out)
