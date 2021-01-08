import base64

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as cfg_constants
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import NAME, SUBNETS, SUBNET_ID, SECURITY_GROUP_ID, KEY_PAIR, PATH, INSTANCE_ID_LIST, EIP
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


class Test_tina_5734(OscTestSuite):

    def test_T5059_set_enable_and_reboot_instances(self):
        # Related to JIRA TINA-5734
        vpc_info = None
        inst = None
        eip = None
        associated = False
        try:
            # create VPC
            vpc_info = create_vpc(self.a1_r1, cidr_prefix='10.0', nb_subnet=1, nb_instance=1, igw=True, state='running',
                                  tags=[{'Key': 'osc.fcu.enable_lan_security_groups', 'Value': '1'}],
                                  no_ping=False)

            resp = self.a1_r1.intel.instance.find(id=vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0]).response
            userdata = """-----BEGIN OUTSCALE SECTION-----
            pin={}
            -----END OUTSCALE SECTION-----""".format(resp.result[0].servers[0].server)

            # run instance
            inst = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region._conf[cfg_constants.CENTOS7],
                                               InstanceType=self.a1_r1.config.region.get_info(cfg_constants.DEFAULT_INSTANCE_TYPE),
                                               MaxCount='1',
                                               MinCount='1',
                                               SecurityGroupId=vpc_info[SUBNETS][0][SECURITY_GROUP_ID],
                                               SubnetId=vpc_info[SUBNETS][0][SUBNET_ID],
                                               KeyName=vpc_info[KEY_PAIR][NAME],
                                               UserData=base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
                                              ).response
            eip = self.a1_r1.fcu.AllocateAddress()
            ret = self.a1_r1.fcu.DescribeAddresses(PublicIp=[eip.response.publicIp])
            eip_allo_id = ret.response.addressesSet[0].allocationId
            self.a1_r1.fcu.AssociateAddress(AllocationId=eip_allo_id, InstanceId=inst.instancesSet[0].instanceId)
            associated = True
            wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[inst.instancesSet[0].instanceId], state='ready')

            # check ssh
            sshclient_1 = SshTools.check_connection_paramiko(vpc_info[SUBNETS][0][EIP]['publicIp'], vpc_info[KEY_PAIR][PATH],
                                                             username=self.a1_r1.config.region.get_info(cfg_constants.CENTOS_USER))
            out, _, _ = SshTools.exec_command_paramiko(sshclient_1, 'pwd')
            sshclient_2 = SshTools.check_connection_paramiko(eip.response.publicIp, vpc_info[KEY_PAIR][PATH],
                                                             username=self.a1_r1.config.region.get_info(cfg_constants.CENTOS_USER))
            out, _, _ = SshTools.exec_command_paramiko(sshclient_2, 'pwd')

            # Stop inst 1
            self.a1_r1.fcu.StopInstances(InstanceId=vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0])
            wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0]], state='stopped')

            # check inst 2
            out, _, _ = SshTools.exec_command_paramiko(sshclient_2, 'pwd')
            self.logger.debug(out)

            # Stop inst 2
            self.a1_r1.fcu.StopInstances(InstanceId=inst.instancesSet[0].instanceId)
            wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[inst.instancesSet[0].instanceId], state='stopped')

            # Start inst 1
            self.a1_r1.fcu.StartInstances(InstanceId=vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0])
            wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0]], state='ready')

            # check inst 1
            sshclient_1 = SshTools.check_connection_paramiko(vpc_info[SUBNETS][0][EIP]['publicIp'], vpc_info[KEY_PAIR][PATH],
                                                             username=self.a1_r1.config.region.get_info(cfg_constants.CENTOS_USER))
            out, _, _ = SshTools.exec_command_paramiko(sshclient_1, 'pwd')
            self.logger.debug(out)

        finally:
            if associated:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=eip.response.publicIp)
            if eip:
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.response.publicIp)
            if inst:
                self.a1_r1.fcu.TerminateInstances(InstanceId=[inst.instancesSet[0].instanceId])
                wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[inst.instancesSet[0].instanceId], state='terminated')
            if vpc_info:
                delete_vpc(self.a1_r1, vpc_info)
