# -*- coding: utf-8 -*-
import re
import pytest
from qa_test_tools.config import config_constants as constants
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances, create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_vpc
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, KEY_PAIR, PATH, INSTANCE_ID_LIST, SUBNETS, EIP
from qa_common_tools.ssh import SshTools
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from time import sleep


class Test_ntp(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info = {}
        cls.vpc_info = None
        super(Test_ntp, cls).setup_class()
        try:
            cls.inst_info['centos7'] = create_instances(osc_sdk=cls.a1_r1, omi_id=cls.a1_r1.config.region.get_info(constants.CENTOS7))
            cls.inst_info['ubuntu'] = create_instances(osc_sdk=cls.a1_r1, omi_id=cls.a1_r1.config.region.get_info(constants.UBUNTU))
            cls.vpc_info = create_vpc(cls.a1_r1, nb_instance=1, state='')
        except Exception:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info:
                for _, inst_info in list(cls.inst_info.items()):
                    delete_instances(cls.a1_r1, inst_info)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_ntp, cls).teardown_class()

    def _test_centos_ntp(self, ipAddress, keyPath):
        sshclient = SshTools.check_connection_paramiko(ipAddress, keyPath, username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        retry = 3
        missing = False
        for _ in range(retry):
            out, _, _ = SshTools.exec_command_paramiko_2(sshclient, 'chronyc -n sources')
            self.logger.info('output --> {}'.format(out))
            for ipaddress in self.a1_r1.config.region.get_info(constants.NTP_SERVERS):
                if not re.search(r'(\*|-|\+) ({})'.format(ipaddress), out):
                    missing = True
            if not missing:
                break
            missing = False
            sleep(10)
        if missing:
            assert False, "Could not find all expected Outscale NTP servers : {}".format(self.a1_r1.config.region.get_info(constants.NTP_SERVERS))

    @pytest.mark.tag_redwire
    def test_T1567_ntp_centos7(self):
        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[self.inst_info['centos7'][INSTANCE_ID_LIST][0]], state='ready')
        self._test_centos_ntp(ipAddress=self.inst_info['centos7'][INSTANCE_SET][0]['ipAddress'], keyPath=self.inst_info['centos7'][KEY_PAIR][PATH])

    @pytest.mark.tag_redwire
    def test_T3584_ntp_centos7_vpc(self):
        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0]], state='ready')
        self._test_centos_ntp(ipAddress=self.vpc_info[SUBNETS][0][EIP]['publicIp'], keyPath=self.vpc_info[KEY_PAIR][PATH])

    @pytest.mark.tag_redwire
    @pytest.mark.region_ubuntu
    def test_T1568_ntp_ubuntu(self):
        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[self.inst_info['ubuntu'][INSTANCE_ID_LIST][0]], state='ready')
        sshclient = SshTools.check_connection_paramiko(self.inst_info['ubuntu'][INSTANCE_SET][0]['ipAddress'],
                                                       self.inst_info['ubuntu'][KEY_PAIR][PATH],
                                                       username=self.a1_r1.config.region.get_info(constants.UBUNTU_USER))
        cmd = "sudo cat /run/systemd/timesyncd.conf.d/01-dhclient.conf"
        SshTools.exec_command_paramiko_2(sshclient, "sudo dhclient -v", expected_status=-1)
        sleep(10)
        out, status, err = SshTools.exec_command_paramiko_2(sshclient, cmd, expected_status=-1)
        self.logger.info('output --> {}'.format(out))
        self.logger.info('status --> {}'.format(status))
        self.logger.info('err --> {}'.format(err))
        if re.search('# NTP server entries received from DHCP server', out):
            for addr in self.a1_r1.config.region.get_info(constants.NTP_SERVERS):
                if not addr in out:
                    assert False, "Missing Outscale NTP server :{}".format(addr)
