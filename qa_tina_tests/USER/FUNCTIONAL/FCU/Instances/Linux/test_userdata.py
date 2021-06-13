import base64
import zlib

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, KEY_PAIR, PATH
from qa_tina_tools.tina import check_tools


class Test_userdata(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_userdata, cls).setup_class()
        try:
            cls.user_data = '''#!/usr/bin/bash
echo "yes" > /tmp/userdata.txt
'''
        except Exception as error:
            cls.teardown_class()
            raise error

    def check_user_data(self, inst_info, gzip=False, decode=True):
        sshclient = check_tools.check_ssh_connection(self.a1_r1, inst_info[INSTANCE_SET][0]['instanceId'],
                                                     inst_info[INSTANCE_SET][0]['ipAddress'], inst_info[KEY_PAIR][PATH],
                                                     self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        _, _, _ = SshTools.exec_command_paramiko(sshclient, 'curl http://169.254.169.254/latest/user-data --output user-data', decode=decode)
        out, _, _ = SshTools.exec_command_paramiko(sshclient, 'cat user-data', decode=decode)
        if gzip:
            self.logger.debug(zlib.decompress(out))
            out = zlib.decompress(out).decode('utf-8')
        assert out.replace("\r\n", "\n") == self.user_data
        if not gzip:
            out, _, _ = SshTools.exec_command_paramiko(sshclient, 'cat /tmp/userdata.txt')
            assert out.startswith('yes')

    def test_T4619_userdata_base64_str(self):
        inst_info = None
        try:
            inst_info = create_instances(self.a1_r1, state='ready',
                                         user_data=base64.b64encode(self.user_data.encode('utf-8')).decode('utf-8'))
            self.check_user_data(inst_info)
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T4620_userdata_base64_gzip(self):
        inst_info = None
        try:
            inst_info = create_instances(self.a1_r1, state='ready',
                                         user_data=base64.b64encode(zlib.compress(self.user_data.encode('utf-8'))).decode('utf-8'))
            self.check_user_data(inst_info, gzip=True, decode=False)
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
