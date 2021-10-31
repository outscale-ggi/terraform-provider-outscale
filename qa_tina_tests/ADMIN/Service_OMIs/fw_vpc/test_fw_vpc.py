import os
import re
import time

from netaddr import IPNetwork, IPAddress
import pytest

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_tina_tools.tina import check_tools


class Test_fw_vpc(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        super(Test_fw_vpc, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, nb_instance=1, igw=True)

            ret = cls.a1_r1.intel.netimpl.firewall.find_firewalls(resource=cls.vpc_info[VPC_ID])
            inst_id = ret.response.result.master.vm

            ret = cls.a1_r1.intel.nic.find(filters={'vm': inst_id})

            inst_ip = None
            for nic in ret.response.result:
                if IPAddress(nic.ips[0].ip) in IPNetwork(cls.a1_r1.config.region.get_info(constants.FW_ADMIN_SUBNET)):
                    inst_ip = nic.ips[0].ip
            assert inst_ip

            cls.sshclient = check_tools.check_ssh_connection(cls.a1_r1, inst_id, inst_ip,
                                                             os.path.expanduser(cls.a1_r1.config.region.get_info(constants.FW_KP)),
                                                             'root', retry=30, timeout=10)

        except Exception as error:
            cls.teardown_class()
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_fw_vpc, cls).teardown_class()

    def test_T1865_check_agent(self):
        assert SshTools.check_service(self.sshclient, 'osc-agent')

    def test_T1867_check_dns(self):
        resolvconf, _, _ = SshTools.exec_command_paramiko(self.sshclient, "cat /etc/resolv.conf")
        for dns in self.a1_r1.config.region.get_info(constants.FW_DNS_SERVERS):
            assert 'nameserver {}'.format(dns) in resolvconf
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, 'grep -c "querylog[[:blank:]]*no;" /etc/named.conf')
        assert int(out) == 1

    def test_T1868_check_ntp(self):
        retry = 30
        wait = 30
        for i in range(retry):
            out, _, _ = SshTools.exec_command_paramiko(self.sshclient, 'chronyc sources')
            if re.search(r'\*({})'.format('|'.join(self.a1_r1.config.region.get_info(constants.FW_NTP_SERVER_PREFIX))), out):
                break
            if i == retry - 1:
                pytest.fail("NTP sync failed: {}".format(out))
            time.sleep(wait)

    def test_T1869_check_zabbix(self):
        assert SshTools.check_service(self.sshclient, 'zabbix-agent', 'zabbix_agent|running')

    def test_T1870_check_consul(self):
        assert SshTools.check_service(self.sshclient, 'consul')

    def test_T1871_check_salt(self):
        assert SshTools.check_service(self.sshclient, 'salt-minion')

    def test_T1873_check_zebra(self):
        # assert SshTools.check_service(self.sshclient, 'zebra')
        pass

    def test_T1874_check_ospfd(self):
        # assert SshTools.check_service(self.sshclient, 'ospfd')
        pass

    def test_T1875_check_netns(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "ip netns exec igw ifconfig")
        assert re.search('lo', out)
        assert re.search('{}'.format(self.vpc_info[VPC_ID]), out)
        assert re.search('wan', out)
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "ip netns exec {} ifconfig".format(self.vpc_info[VPC_ID]))
        assert re.search('lo', out)
        assert re.search('s-', out)
        assert re.search('ifw', out)
        assert re.search('igw', out)
        # TODO: Add tests
        # out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "ip netns exec igw iptables -L")
        # print out
        # out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "ip netns exec {} iptables -L".format(self.vpc_info[VPC_ID]))
        # print out
        # out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "ip netns exec igw ip route")
        # print out
        # out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "ip netns exec {} ip route".format(self.vpc_info[VPC_ID]))
        # print out

    def test_T1878_check_fdcp(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "ps ax | grep dhcp")
        pattern = re.compile('/usr/local/outscale/virtualenv36/bin/fdhcp')
        assert re.search(pattern, out)

    def test_T1876_check_hostname(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "hostname")
        pattern = re.compile('fw-master-{}'.format(self.vpc_info[VPC_ID]))
        assert re.search(pattern, out)

    def test_T1877_check_kernel(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "uname -a")
        pattern = re.compile(' 4.19.141 ')
        assert re.search(pattern, out)

    def test_T1926_check_cpu_generation(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "cat /proc/cpuinfo")
        pattern = re.compile('Sandy Bridge')
        assert re.search(pattern, out)
