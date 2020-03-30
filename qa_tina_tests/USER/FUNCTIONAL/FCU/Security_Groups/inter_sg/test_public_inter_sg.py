import time
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.config import config_constants as constants

from qa_tina_tools.constants import SG_WAIT_TIME
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances_old, create_keypair
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old, delete_keypair
from qa_tina_tools.tina.info_keys import NAME, PATH
from qa_common_tools.ssh import SshTools
import base64

NUM_PER_TRY = 10
NUM_TRY = 10


class Test_public_inter_sg(OscTestSuite):

    @classmethod
    def setup_class(cls):

        cls.kp_info = None
        cls.inst1_id = None
        cls.inst2_id = None
        cls.sg1_id = None
        cls.sg2_id = None
        cls.QUOTAS = {'vm_limit': NUM_PER_TRY * NUM_TRY + 1}
        super(Test_public_inter_sg, cls).setup_class()
        try:
            cls.kp_info = create_keypair(cls.a1_r1)
            cls.sg1_name = id_generator(prefix='sg1')
            cls.sg2_name = id_generator(prefix='sg2')
            ret = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription=cls.sg1_name, GroupName=cls.sg1_name)
            cls.sg1_id = ret.response.groupId
            ret = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription=cls.sg2_name, GroupName=cls.sg2_name)
            cls.sg2_id = ret.response.groupId
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=cls.sg1_id, IpProtocol='tcp', FromPort=22,
                                                        ToPort=22, CidrIp=Configuration.get('cidr', 'allips'))
            subnets = cls.a1_r1.intel.subnet.describe(filters={'network': 'vpc-00000000'})
            if subnets.response.result.count < 2:
                cls.logger.inofo("Test can not be executed")
            userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.internal.private-subnet-id-force={}
            -----END OUTSCALE SECTION-----""".format(subnets.response.result.results[0].id)
            ret, _ = create_instances_old(cls.a1_r1, security_group_id_list=[cls.sg1_id], key_name=cls.kp_info[NAME],
                                          user_data=base64.b64encode(userdata.encode('utf-8')).decode('utf-8'), state='running')
            cls.inst1 = ret.response.reservationSet[0].instancesSet[0]
            userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.internal.private-subnet-id-force={}
            -----END OUTSCALE SECTION-----""".format(subnets.response.result.results[1].id)
            ret, cls.inst2_id = create_instances_old(cls.a1_r1, security_group_id_list=[cls.sg2_id], key_name=cls.kp_info[NAME],
                                                     user_data=base64.b64encode(userdata.encode('utf-8')).decode('utf-8'), state='running')
            cls.inst2 = ret.response.reservationSet[0].instancesSet[0]
            cls.sshclient = SshTools.check_connection_paramiko(cls.inst1.ipAddress, cls.kp_info[PATH],
                                                               username=cls.a1_r1.config.region.get_info(constants.CENTOS_USER))

        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.kp_info:
                delete_keypair(cls.a1_r1, cls.kp_info)
            if cls.inst1.instanceId:
                delete_instances_old(cls.a1_r1, [cls.inst1.instanceId])
            if cls.inst2.instanceId:
                delete_instances_old(cls.a1_r1, [cls.inst2.instanceId])

            if cls.sg1_id:
                cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.sg1_id)
            if cls.sg2_id:
                cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.sg2_id)
        finally:
            super(Test_public_inter_sg, cls).teardown_class()

    def test_T300_rule_with_public_ip(self):
        self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.sg2_id, IpProtocol='icmp',
                                                     FromPort=-1, ToPort=-1, CidrIp=self.inst1.ipAddress + '/32')
        time.sleep(SG_WAIT_TIME)
        try:
            out, _, _ = SshTools.exec_command_paramiko_2(self.sshclient, 'ping -c 1 -W 1 {}'.format(self.inst2.ipAddress), retry=10)
            assert "1 packets transmitted, 1 received, 0% packet loss" in out
            out, _, _ = SshTools.exec_command_paramiko_2(self.sshclient, 'ping -c 1 -W 1 {}'.format(self.inst2.privateIpAddress), retry=10)
            assert "1 packets transmitted, 1 received, 0% packet loss" in out
        finally:
            self.a1_r1.fcu.RevokeSecurityGroupIngress(GroupId=self.sg2_id, IpProtocol='icmp',
                                                      FromPort=-1, ToPort=-1, CidrIp=self.inst1.ipAddress + '/32')
            time.sleep(SG_WAIT_TIME)

    def test_T299_rule_with_private_ip(self):
        self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.sg2_id, IpProtocol='icmp',
                                                     FromPort=-1, ToPort=-1, CidrIp=self.inst1.privateIpAddress + '/32')

        time.sleep(SG_WAIT_TIME)
        try:
            out, _, _ = SshTools.exec_command_paramiko_2(self.sshclient, 'ping -c 1 -W 1 {}'.format(self.inst2.privateIpAddress), retry=10)
            assert "1 packets transmitted, 1 received, 0% packet loss" in out
            out, _, _ = SshTools.exec_command_paramiko_2(self.sshclient, 'ping -c 1 -W 1 {}'.format(self.inst2.ipAddress),
                                                         retry=10, expected_status=-1)
            # assert "1 packets transmitted, 1 received, 0% packet loss" in out
            assert "1 packets transmitted, 0 received, 100% packet loss" in out
        finally:
            self.a1_r1.fcu.RevokeSecurityGroupIngress(GroupId=self.sg2_id, IpProtocol='icmp',
                                                      FromPort=-1, ToPort=-1, CidrIp=self.inst1.privateIpAddress + '/32')
            time.sleep(SG_WAIT_TIME)
