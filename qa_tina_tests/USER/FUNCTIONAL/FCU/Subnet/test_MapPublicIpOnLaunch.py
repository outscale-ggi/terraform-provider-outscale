from qa_test_tools.config import config_constants as constants

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, INSTANCE_ID_LIST, PATH, KEY_PAIR
from qa_common_tools.ssh import SshTools
from qa_tina_tools.tools.tina.info_keys import VPC_ID, SUBNETS, SUBNET_ID


class Test_MapPublicIpOnLaunch(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_MapPublicIpOnLaunch, cls).setup_class()
        cls.instance_info = None
        cls.vpc_info = None
        cls.inst_id = None
        try:
            cls.vpc_info = create_vpc(osc_sdk=cls.a1_r1)
            cls.subnet_id = cls.vpc_info[SUBNETS][0][SUBNET_ID]



        except Exception:
            try:
                cls.teardown_class()
            except  :
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.instance_info:
                delete_instances(cls.a1_r1, cls.instance_info)
            if cls.vpc_info:
                cleanup_vpcs(cls.a1_r1, vpc_id_list=[cls.vpc_info[VPC_ID]])
        finally:
            super(Test_MapPublicIpOnLaunch, cls).teardown_class()

    def test_T4383_with_valid_param(self):
        self.a1_r1.fcu.ModifySubnetAttribute(MapPublicIpOnLaunch={'Value': 'true'}, SubnetId=self.subnet_id)
        self.instance_info = create_instances(self.a1_r1, subnet_id=self.subnet_id, state='ready')
        self.inst_id = self.instance_info[INSTANCE_ID_LIST][0]
        ret = self.a1_r1.fcu.DescribeInstances(InstanceId=self.inst_id)
        ip = ret.response.reservationSet[0].instancesSet[0].ipAddress
        self.instance_info[INSTANCE_SET][0]
        kp_info = self.instance_info[KEY_PAIR]

        connection = SshTools.check_connection_paramiko(ip, kp_info[PATH],
                                                        self.a1_r1.config.region.get_info(constants.CENTOS_USER))

        cmd = 'pwd'
        out, status, _ = SshTools.exec_command_paramiko_2(connection, cmd)
        self.logger.info(out)
        assert not status, "SSH command was not executed correctly on the remote host"

