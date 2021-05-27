# -*- coding: utf-8 -*-

import time

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, INSTANCE_SET, KEY_PAIR, PATH, SUBNETS, VPC_ID
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_tina_tools.tina import check_tools


class Test_firewall_vpc(OscTestSuite):
    @classmethod
    def setup_class(cls):
        super(Test_firewall_vpc, cls).setup_class()
        cls.vpc_info = None
        cls.eip_allo_id = None
        cls.public_ip = None
        cls.inst_id = None

    @classmethod
    def teardown_class(cls):
        super(Test_firewall_vpc, cls).teardown_class()

    def setup_method(self, method):
        super(Test_firewall_vpc, self).setup_method(method)
        self.vpc_info = None
        self.eip_allo_id = None
        self.public_ip = None
        try:
            self.vpc_info = create_vpc(osc_sdk=self.a1_r1, nb_instance=1, state='running', no_eip=True)
            ret = self.a1_r1.fcu.AllocateAddress()
            self.public_ip = ret.response.publicIp
            ret = self.a1_r1.fcu.DescribeAddresses(PublicIp=[ret.response.publicIp])
            self.eip_allo_id = ret.response.addressesSet[0].allocationId
            self.inst_id = self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0]

            ret = self.a1_r1.fcu.AssociateAddress(AllocationId=self.eip_allo_id, InstanceId=self.inst_id)
            wait_instances_state(self.a1_r1, self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST], state='ready')
        except Exception as error:
            try:
                self.teardown_method(method)
            finally:
                raise error

    def teardown_method(self, method):
        try:
            if self.eip_allo_id:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.public_ip)
            if self.public_ip:
                self.a1_r1.fcu.ReleaseAddress(PublicIp=self.public_ip)
            if self.vpc_info:
                delete_vpc(self.a1_r1, self.vpc_info)
        finally:
            super(Test_firewall_vpc, self).teardown_method(method)

    def test_T1533_spwan_firewall_VPC(self):
        sshclient = check_tools.check_ssh_connection(self.a1_r1, self.inst_id, self.public_ip, self.vpc_info[KEY_PAIR][PATH],
                                                     self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        out, _, _ = SshTools.exec_command_paramiko(
            sshclient, 'ping -W 1 -c 1 {}'.format(self.vpc_info[SUBNETS][0][INSTANCE_SET][0]['privateIpAddress']), retry=5, timeout=5)
        assert "1 packets transmitted, 1 received, 0% packet loss" in out

        ret = self.a1_r1.intel.netimpl.firewall.get_firewalls(resource=self.vpc_info[VPC_ID])
        inst_id = ret.response.result.master.vm

        self.a1_r1.intel.instance.shutdown(owner=self.a1_r1.config.region.get_info(constants.FW_OWNER), instance_ids=[inst_id], force=True)
        self.a1_r1.intel.instance.terminate(owner=self.a1_r1.config.region.get_info(constants.FW_OWNER), instance_ids=[inst_id])

        time.sleep(15)

        self.a1_r1.intel.netimpl.create_firewalls(resource=self.vpc_info[VPC_ID])

        sshclient = check_tools.check_ssh_connection(self.a1_r1, self.inst_id, self.public_ip, self.vpc_info[KEY_PAIR][PATH],
                                                     self.a1_r1.config.region.get_info(constants.CENTOS_USER), retry=20, timeout=10)

        out, _, _ = SshTools.exec_command_paramiko(
            sshclient, 'ping -W 1 -c 1 {}'.format(self.vpc_info[SUBNETS][0][INSTANCE_SET][0]['privateIpAddress']), retry=5, timeout=5)
        assert "1 packets transmitted, 1 received, 0% packet loss" in out

    def test_T1925_stop_start_firewall_VPC(self):
        sshclient = check_tools.check_ssh_connection(self.a1_r1, self.inst_id, self.public_ip, self.vpc_info[KEY_PAIR][PATH],
                                                     self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        out, _, _ = SshTools.exec_command_paramiko(
            sshclient, 'ping -W 1 -c 1 {}'.format(self.vpc_info[SUBNETS][0][INSTANCE_SET][0]['privateIpAddress']), retry=5, timeout=5)
        assert "1 packets transmitted, 1 received, 0% packet loss" in out

        ret = self.a1_r1.intel.netimpl.firewall.get_firewalls(resource=self.vpc_info[VPC_ID])
        inst_id = ret.response.result.master.vm

        self.a1_r1.intel.instance.shutdown(owner=self.a1_r1.config.region.get_info(constants.FW_OWNER), instance_ids=[inst_id], force=True)

        time.sleep(15)

        self.a1_r1.intel.instance.start(owner=self.a1_r1.config.region.get_info(constants.FW_OWNER), instance_ids=[inst_id])

        sshclient = check_tools.check_ssh_connection(self.a1_r1, self.inst_id, self.public_ip, self.vpc_info[KEY_PAIR][PATH],
                                                     self.a1_r1.config.region.get_info(constants.CENTOS_USER), retry=20, timeout=10)

        out, _, _ = SshTools.exec_command_paramiko(
            sshclient, 'ping -W 1 -c 1 {}'.format(self.vpc_info[SUBNETS][0][INSTANCE_SET][0]['privateIpAddress']), retry=5, timeout=5)
        assert "1 packets transmitted, 1 received, 0% packet loss" in out
