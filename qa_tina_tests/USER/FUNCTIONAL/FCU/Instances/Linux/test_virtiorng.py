from osc_common.exceptions import OscApiException
from qa_common_tools.config import config_constants as constants

from qa_common_tools.misc import assert_error
from qa_common_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, INSTANCE_SET, KEY_PAIR, PATH
from qa_common_tools.ssh import SshTools


class Test_virtiorng(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        super(Test_virtiorng, cls).setup_class()
        try:
            cls.inst_info = create_instances(cls.a1_r1, state='ready')
        except Exception as error:
            try:
                cls.teardown_class()
            except:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_virtiorng, cls).teardown_class()

    def test_T4597_virtio_rng(self):
        inst = self.inst_info[INSTANCE_SET][0]
        kp_info = self.inst_info[KEY_PAIR]

        connection = SshTools.check_connection_paramiko(inst['ipAddress'], kp_info[PATH],
                                                        self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        cmd = "cat /sys/devices/virtual/misc/hw_random/rng_available"
        out, status, error = SshTools.exec_command_paramiko_2(connection, cmd)
        if out == "\r\n":
            known_error('TINA-5335', 'this new functionality virtio rng caused this regression')
        else:
            assert False, 'remove known error'
        assert 'virtio' in out
        cmd = "cat /sys/devices/virtual/misc/hw_random/rng_current"
        out, status, error = SshTools.exec_command_paramiko_2(connection, cmd)
        assert 'virtio' in out