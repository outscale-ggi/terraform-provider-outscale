
import os
import re
import time

from netaddr import IPNetwork, IPAddress
import pytest

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import id_generator
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.delete_tools import delete_lbu
from qa_tina_tools.tina import check_tools


class Test_fw_lbu(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_fw_lbu, cls).setup_class()
        try:
            cls.lb_name = id_generator('lbu')
            cls.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                             LoadBalancerName=cls.lb_name, AvailabilityZones=[cls.a1_r1.config.region.az_name])

            time.sleep(10)  # TODO: rm this line...
            ret = cls.a1_r1.intel_lbu.lb.get(owner=cls.a1_r1.config.account.account_id,
                                             names=[cls.lb_name])

            inst_id = ret.response.result[0].lbu_instance

            ret = cls.a1_r1.intel.nic.find(filters={'vm': inst_id})

            inst_ip = None
            for nic in ret.response.result:
                if IPAddress(nic.ips[0].ip) in IPNetwork(cls.a1_r1.config.region.get_info(constants.FW_ADMIN_SUBNET)):
                    inst_ip = nic.ips[0].ip
            assert inst_ip

            cls.sshclient = check_tools.check_ssh_connection(cls.a1_r1, inst_id, inst_ip,
                                                             os.path.expanduser(cls.a1_r1.config.region.get_info(constants.FW_KP)),
                                                             'root', retry=30, timeout=10)
        except Exception:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            delete_lbu(cls.a1_r1, lbu_name=cls.lb_name)
        finally:
            super(Test_fw_lbu, cls).teardown_class()

    def test_T1879_check_agent(self):
        assert SshTools.check_service(self.sshclient, 'osc-lbu-agent', retry=10)

    def test_T1881_check_dns(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "cat /etc/resolv.conf")
        for dns in self.a1_r1.config.region.get_info(constants.FW_DNS_SERVERS):
            pattern = re.compile('nameserver {}'.format(dns))
            assert re.search(pattern, out)

    def test_T1882_check_ntp(self):
        retry = 30
        wait = 30
        for i in range(retry):
            out, _, _ = SshTools.exec_command_paramiko(self.sshclient, 'ntpq -pn')
            if re.search(r'\*({})'.format('|'.join(self.a1_r1.config.region.get_info(constants.FW_NTP_SERVER_PREFIX))), out):
                break
            if i == retry - 1:
                pytest.fail("NTP sync failed: {}".format(out))
            time.sleep(wait)

    def test_T1884_check_consul(self):
        assert SshTools.check_service(self.sshclient, 'consul')

    def test_T1885_check_salt(self):
        assert SshTools.check_service(self.sshclient, 'salt-minion')

    def test_T1886_check_haproxy(self):
        assert SshTools.check_service(self.sshclient, 'haproxy')

    # def test_T000_check_netns(self):
    #    ???

    def test_T1890_check_hostname(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "hostname")
        pattern = re.compile('lbu-{}'.format(self.lb_name))
        assert re.search(pattern, out)

    def test_T1891_check_kernel(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "uname -a")
        pattern = re.compile(' {} '.format(self.a1_r1.config.region.get_info(constants.FW_LBU_KERNEL_VERSION)))
        assert re.search(pattern, out)

    def test_T1928_check_cpu_generation(self):
        out, _, _ = SshTools.exec_command_paramiko(self.sshclient, "cat /proc/cpuinfo")
        pattern = re.compile('Sandy Bridge')
        assert re.search(pattern, out)
