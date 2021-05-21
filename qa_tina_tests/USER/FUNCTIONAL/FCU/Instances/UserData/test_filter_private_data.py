import base64

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.ssh import SshTools
from qa_test_tools import misc
from qa_test_tools.config import config_constants
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina import info_keys
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tina import check_tools


@pytest.mark.region_admin
class Test_filter_private_data(OscTestSuite):

    def test_T5579_filter_private_data(self):

        user_data = '-----BEGIN OUTSCALE SECTION-----\nfilter_private_section=true\n-----END OUTSCALE SECTION-----\nThis is some public data'

        inst_info = None

        try:
            inst_info = create_instances(self.a1_r1, state='ready', user_data=base64.b64encode(user_data.encode('utf-8')).decode('utf-8'))

            sshclient = check_tools.check_ssh_connection(self.a1_r1, inst_info[info_keys.INSTANCE_SET][0]['instanceId'],
                                                         inst_info[info_keys.INSTANCE_SET][0]['ipAddress'],
                                                         inst_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                         self.a1_r1.config.region.get_info(config_constants.CENTOS_USER))
            out, _, _ = SshTools.exec_command_paramiko(sshclient, 'curl http://169.254.169.254/latest/user-data', decode=True)

            print(out)
            assert out == 'This is some public data'
        except OscApiException as error:
            misc.assert_error(error, 400, 'OWS.Error', 'Invalid tag name filter_private_section')
            known_error('TINA-????', 'private section filtering does not function in ows')
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
