from __future__ import division

import datetime
import sys
import time

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_keypair
from qa_tina_tools.tools.tina.delete_tools import delete_keypair
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_tina_tools.tools.tina import info_keys
from qa_tina_tools.tina import check_tools


def write_n_bytes_to_console(size_console=0, max_size_in_bytes=65536):
    list_strings = []

    size_string_python = 37
    size_of_chuncks = 100  # size of bytes of each chuck of text

    string_length = max_size_in_bytes - size_console

    string_length_divided = string_length / size_of_chuncks

    for _ in range(string_length_divided):
        list_strings.append(id_generator(size=(size_of_chuncks - size_string_python)))

    return list_strings


class Test_ConsoleThrottling(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ConsoleThrottling, cls).setup_class()
        time_now = datetime.datetime.now()
        unique_id = time_now.strftime('%Y%m%d%H%M%S')
        cls.sg_name = 'sg_test_T55_{}'.format(unique_id)
        ip_ingress = Configuration.get('cidr', 'allips')

        cls.public_ip_inst = None
        cls.inst_id = None

        instance_type = cls.a1_r1.config.region.get_info('default_instance_type')
        cls.kp_info = None
        cls.sshclient = None

        try:
            # create security group
            sg_response = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=cls.sg_name)

            sg_id = sg_response.response.groupId

            # authorize rules
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupName=cls.sg_name, IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp=ip_ingress)

            # create keypair
            cls.kp_info = create_keypair(cls.a1_r1)

            # run instance
            inst = cls.a1_r1.fcu.RunInstances(ImageId=cls.a1_r1.config.region.get_info('centos7'), MaxCount='1',
                                              MinCount='1',
                                              SecurityGroupId=sg_id, KeyName=cls.kp_info[info_keys.NAME],
                                              InstanceType=instance_type)

            # get instance ID
            cls.inst_id = inst.response.instancesSet[0].instanceId

            # wait instance to become ready
            wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=[cls.inst_id], state='ready', threshold=60, wait_time=5)

            # get public IP
            describe_res = cls.a1_r1.fcu.DescribeInstances(Filter=[{'Name': 'instance-id', 'Value': [cls.inst_id]}])
            cls.public_ip_inst = describe_res.response.reservationSet[0].instancesSet[0].ipAddress

            cls.sshclient = check_tools.check_ssh_connection(cls.a1_r1, cls.inst_id, cls.public_ip_inst, cls.kp_info[info_keys.PATH],
                                                             cls.a1_r1.config.region.get_info(constants.CENTOS_USER))

        except Exception as error:
            cls.teardown_class()
            raise error

    @classmethod
    def teardown_class(cls):
        try:

            # terminate the instance
            cls.a1_r1.fcu.TerminateInstances(InstanceId=[cls.inst_id])

            # replace by wait function
            wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=[cls.inst_id], state='terminated')

            cls.a1_r1.fcu.DeleteKeyPair(KeyName=cls.kp_info[info_keys.NAME])

            cls.a1_r1.fcu.DeleteSecurityGroup(GroupName=cls.sg_name)

            delete_keypair(cls.a1_r1, cls.kp_info)

        finally:
            super(Test_ConsoleThrottling, cls).teardown_class()

    # TODO rename with test_T....
    def console_throttling(self):
        ret = self.a1_r1.fcu.GetConsoleOutput(InstanceId=self.inst_id)
        console_output = ret.response.output
        # output_decoded = base64.b64decode(OutConsol).decode("utf-8")

        list_to_write = write_n_bytes_to_console(size_console=sys.getsizeof(console_output), max_size_in_bytes=65536)

        for elt in list_to_write:
            cmd = "echo \'{}\' > /dev/kmsg".format(elt)
            out, _, _ = SshTools.exec_command_paramiko(self.sshclient, cmd)
            self.logger.info(out)

        time.sleep(20)
        ret = self.a1_r1.fcu.GetConsoleOutput(InstanceId=self.inst_id)
        # console_output = ret.response.output
        # output_decoded = base64.b64decode(console_output).decode("utf-8")
