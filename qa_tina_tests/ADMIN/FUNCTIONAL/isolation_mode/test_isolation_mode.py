from time import sleep

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.ssh import SshTools, OscCommandError
from qa_test_tools.config import config_constants as cfg_constants
from qa_test_tools.config.configuration import Configuration
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_vpc, start_instances
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.wait_tools import wait_instance_service_state, wait_instances_state
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_tina_tools.tools.tina import info_keys
from qa_tina_tools.tina import check_tools


class Test_isolation_mode(OscTinaTest):

    def test_T5797_vxlanvpc_to_ovsvpc(self):
        fw_vm = None
        # create a vpc with two vms
        try:
            vpc_info = create_vpc(self.a1_r1, nb_instance=2, state='ready')
            ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id , limit=2, network=vpc_info[VPC_ID])
            assert {call.lifecycle for call in ret.response.result.results} == {'vxlanvpc.vm'}
            priv_ip = ret.response.result.results[0].private_ip
            if ret.response.result.results[0].public_ip is not None:
                priv_ip = ret.response.result.results[1].private_ip
        # check ping inst1 to inst2
            sshclient = check_tools.check_ssh_connection(self.a1_r1, vpc_info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST][0],
                                                           vpc_info[info_keys.SUBNETS][0][info_keys.EIP]['publicIp'],
                                                           vpc_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                           self.a1_r1.config.region.get_info(cfg_constants.CENTOS_USER))
            cmd = "sudo ping " + priv_ip + " -c 1"
            _, status, _ = SshTools.exec_command_paramiko(sshclient, cmd, retry=10)
        # get fw vm and terminate it
            fw_vm = self.a1_r1.intel.netimpl.firewall.get_firewalls(resource=vpc_info[VPC_ID])
        # stop vms
            self.a1_r1.fcu.StopInstances(InstanceId=vpc_info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST], Force=True)
            wait_instances_state(self.a1_r1, vpc_info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST], 'stopped')
        # terminate fw vm
            ret = self.a1_r1.intel.instance.terminate(owner="438422465534", instance_ids=[fw_vm.response.result.master.vm])
            wait_instance_service_state(self.a1_r1, [fw_vm.response.result.master.vm], 'terminated')
        # modify isolation mode
            ret = self.a1_r1.intel.vpc.modify(owner=self.a1_r1.config.account.account_id,
                                              vpc_id=vpc_info[VPC_ID], isolation_mode='ovsvpc', force=True)
        # create vpc fw
            ret = self.a1_r1.intel.netimpl.create_firewalls(resource=vpc_info[VPC_ID])
            wait_instance_service_state(self.a1_r1, [ret.response.result.master.vm], 'ready')
            start_instances(self.a1_r1, vpc_info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST])
            wait_instances_state(self.a1_r1, vpc_info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST], 'ready')
            ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id , limit=2, network=vpc_info[VPC_ID])
        # create check vm cycle and check ping between vms
            assert {call.lifecycle for call in ret.response.result.results} == {'ovsvpc.vm'}
            sshclient = check_tools.check_ssh_connection(self.a1_r1, vpc_info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST][0],
                                                           vpc_info[info_keys.SUBNETS][0][info_keys.EIP]['publicIp'],
                                                           vpc_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                           self.a1_r1.config.region.get_info(cfg_constants.CENTOS_USER))
            cmd = "sudo ping " + priv_ip + " -c 1"
            status = None
            try:
                _, status, _ = SshTools.exec_command_paramiko(sshclient, cmd, retry=10)
            except OscCommandError:
                assert status is None
        # authorize ping between two vms
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=vpc_info[info_keys.SUBNETS][0][info_keys.SECURITY_GROUP_ID],
                                                         IpProtocol='icmp', FromPort='-1', ToPort='-1',
                                                         CidrIp=Configuration.get('cidr', 'allips'))
            sleep(10)
            sshclient = check_tools.check_ssh_connection(self.a1_r1, vpc_info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST][0],
                                                           vpc_info[info_keys.SUBNETS][0][info_keys.EIP]['publicIp'],
                                                           vpc_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                           self.a1_r1.config.region.get_info(cfg_constants.CENTOS_USER))
            cmd = "sudo ping " + priv_ip + " -c 1"
            _, status, _ = SshTools.exec_command_paramiko(sshclient, cmd, retry=10)
        finally:
            if vpc_info:
                delete_vpc(self.a1_r1, vpc_info)

    def test_T5798_with_invalid_vm_state(self):
        #running vm in vpc
        try:
            vpc_info = create_vpc(self.a1_r1, nb_instance=2, state='ready')
            self.a1_r1.intel.vpc.modify(owner=self.a1_r1.config.account.account_id, vpc_id=vpc_info[VPC_ID], isolation_mode='ovsvpc')
        except OscApiException as error:
            assert error.message == 'invalid-state'
        #running fw vpc
        try:
            self.a1_r1.fcu.StopInstances(InstanceId=vpc_info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST], Force=True)
            wait_instances_state(self.a1_r1, vpc_info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST], 'stopped')
            self.a1_r1.intel.vpc.modify(owner=self.a1_r1.config.account.account_id, vpc_id=vpc_info[VPC_ID], isolation_mode='ovsvpc')
        except OscApiException as error:
            assert error.message == 'invalid-state - This change can only applied at VPC creation time'
        finally:
            if vpc_info:
                delete_vpc(self.a1_r1, vpc_info)
