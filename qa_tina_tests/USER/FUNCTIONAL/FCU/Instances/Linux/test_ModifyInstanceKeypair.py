
from qa_tina_tools.tools.tina.create_tools import create_instances, create_keypair
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_keypair
from qa_tina_tools.tools.tina.info_keys import PATH, INSTANCE_ID_LIST, INSTANCE_SET, KEY_PAIR, NAME
from qa_common_tools.ssh import SshTools
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import id_generator
from qa_test_tools.config import config_constants as constants



class Test_ModifyInstanceKeypair(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ModifyInstanceKeypair, cls).setup_class()
        try:
            pass
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_ModifyInstanceKeypair, cls).teardown_class()

    def test_T4137_create_and_modify_instance_keypair(self):
        kp_info = None
        inst_info = None
        try:
            # create instance with keypair and wait_instances_state(osc_sdk=self.a1_r1, state='ready')
            inst_info = create_instances(self.a1_r1, state='ready')
            # ssh on instance
            sshclient = SshTools.check_connection_paramiko(inst_info[INSTANCE_SET][0]['ipAddress'], inst_info[KEY_PAIR][PATH],
                                                           username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # execute command
            cmd = 'curl http://169.254.169.254/latest/meta-data/public-keys/0/openssh-key'
            out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
            self.logger.info(out)
            assert not status, "SSH command was not executed correctly on the remote host"
            # create other keypair
            key_name = id_generator(prefix='kp_')
            kp_info = create_keypair(self.a1_r1, name=key_name)
            # modify instance attribute keypair
            ret = self.a1_r1.fcu.ModifyInstanceKeypair(InstanceId=inst_info[INSTANCE_ID_LIST][0], KeyName=kp_info[NAME])
            assert ret.response.requestId
            # execute command
            cmd = 'curl http://169.254.169.254/latest/meta-data/public-keys/0/openssh-key'
            ret = out, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
            self.logger.info(out)
            assert ret
            assert not status, "SSH command was not executed correctly on the remote host"
        finally:
            try:
                if inst_info:
                    delete_instances(self.a1_r1, inst_info)
                if kp_info:
                    delete_keypair(self.a1_r1, kp_info)
            except Exception as error:
                self.logger.exception(error)
                raise error

