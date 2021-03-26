import base64

import pytest

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina import info_keys
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances


@pytest.mark.region_admin
class Test_filter_private_data(OscTestSuite):


    def test_T5579_filter_private_data(self):

        user_data = '-----BEGIN OUTSCALE SECTION-----\nfilter_private_section=true\n-----END OUTSCALE SECTION-----\nThis is some public data'

        inst_info = None

        try:
            inst_info = create_instances(self.a1_r1, state='ready', user_data=base64.b64encode(user_data.encode('utf-8')).decode('utf-8'))

            sshclient = SshTools.check_connection_paramiko(inst_info[info_keys.INSTANCE_SET][0]['ipAddress'],
                                                           inst_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                           username=self.a1_r1.config.region.get_info(config_constants.CENTOS_USER))
            out, _, _ = SshTools.exec_command_paramiko(sshclient, 'curl http://169.254.169.254/latest/user-data', decode=True)

            print(out)
            assert False, 'TODO, Check output'

        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
