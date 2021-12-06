from datetime import datetime
import subprocess
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import oapi, check_tools, info_keys
from qa_test_tools.config import config_constants


MAX_WAIT_TIME = 240


class Test_port_management(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_port_management, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_port_management, cls).teardown_class()

    def test_T6138_open_close(self):

        def test_ping(ip_address, expected_status, wait_time=MAX_WAIT_TIME):
            start_ping = datetime.now()
            while (datetime.now() - start_ping).total_seconds() < wait_time:
                try:
                    subprocess.check_call(["ping -c 5 %s" % ip_address], shell=True)  # nosec - cannot put shell=True for the moment
                    status = True
                except subprocess.CalledProcessError:
                    status = False
                if status == expected_status:
                    break
            return status == expected_status

        sg_id = None
        vm_info = None
        try:
            sg_id = oapi.create_SecurityGroup(self.a1_r1, no_ping=True)

            vm_info = oapi.create_Vms(self.a1_r1, sg_ids=[sg_id], state='ready')

            check_tools.check_ssh_connection(self.a1_r1, vm_info[info_keys.VM_IDS][0],
                                             vm_info[info_keys.VMS][0]['PublicIp'],
                                             vm_info[info_keys.KEY_PAIR][info_keys.PATH],
                                             self.a1_r1.config.region.get_info(config_constants.CENTOS_USER))

            # verify ping does not function
            assert test_ping(vm_info[info_keys.VMS][0]['PublicIp'], False, wait_time=60), 'Could ping, not expected!'
            # authorize ping
            self.a1_r1.oapi.CreateSecurityGroupRule(SecurityGroupId=sg_id, IpProtocol='icmp',
                                                    FromPortRange=-1, ToPortRange=-1, IpRange='0.0.0.0/0', Flow='Inbound')
            # verify that ping does function
            assert test_ping(vm_info[info_keys.VMS][0]['PublicIp'], True, wait_time=240), 'Could not ping, not expected!'
            # remove ping authorization
            self.a1_r1.oapi.DeleteSecurityGroupRule(SecurityGroupId=sg_id, IpProtocol='icmp',
                                                    FromPortRange=-1, ToPortRange=-1, IpRange='0.0.0.0/0', Flow='Inbound')
            # verify that ping does not function
            assert test_ping(vm_info[info_keys.VMS][0]['PublicIp'], False, wait_time=240), 'Could ping, not expected!'

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if sg_id:
                self.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=sg_id)
