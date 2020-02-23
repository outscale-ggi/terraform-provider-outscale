
from qa_common_tools.constants import CENTOS_USER
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import KEY_PAIR, PATH, INSTANCE_ID_LIST
from qa_common_tools.ssh import SshTools


class Test_associate_EIP(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_associate_EIP, cls).setup_class()

        cls.info = None

        try:
            cls.info = create_instances(cls.a1_r1, state='ready')
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.info:
                delete_instances(cls.a1_r1, cls.info)
        finally:
            super(Test_associate_EIP, cls).teardown_class()

    def test_T121_associate_EIP_Public_Cloud(self):
        eip = None
        try:
            # allocate eip
            eip = self.a1_r1.fcu.AllocateAddress()

            # get allocationID
            ret = self.a1_r1.fcu.DescribeAddresses(PublicIp=[eip.response.publicIp])

            eip_allo_id = ret.response.addressesSet[0].allocationId

            ret = self.a1_r1.fcu.AssociateAddress(AllocationId=eip_allo_id, InstanceId=self.info[INSTANCE_ID_LIST][0])
            public_ip_inst = eip.response.publicIp

            sshclient = SshTools.check_connection_paramiko(public_ip_inst, self.info[KEY_PAIR][PATH],
                                                           username=self.a1_r1.config.region.get_info(CENTOS_USER), retry=4, timeout=10)

            cmd = 'pwd'
            out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
            self.logger.info(out)
            assert not status, "SSH command was not executed correctly on the remote host"

        finally:
            if eip:
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.response.publicIp)
