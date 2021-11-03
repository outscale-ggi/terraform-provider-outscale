import pytest

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_tina_tools.tina import check_tools
from qa_tina_tools.tools.tina import create_tools, delete_tools, info_keys
from qa_tina_tools.test_base import OscTinaTest


class Test_private_linux_instance(OscTinaTest):


    @pytest.mark.tag_redwire
    def test_T112_create_using_linux_instance_vpc(self):

        vpc_info = None
        try:
            vpc_info = create_tools.create_vpc(self.a1_r1, nb_instance=1, state='ready')
            sshclient = check_tools.check_ssh_connection(self.a1_r1, vpc_info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST][0],
                                                         vpc_info[info_keys.SUBNETS][0][info_keys.EIP]['publicIp'],
                                                         vpc_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                         self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            _, status, _ = SshTools.exec_command_paramiko(sshclient, 'pwd')
            # self.logger.info(out)
            assert not status, "SSH command was not executed correctly on the remote host"
        finally:
            if vpc_info:
                delete_tools.delete_vpc(self.a1_r1, vpc_info)
