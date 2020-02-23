from qa_common_tools.constants import CENTOS_USER
from qa_common_tools.misc import id_generator
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, INSTANCE_ID_LIST, PATH, KEY_PAIR
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_common_tools.ssh import SshTools
import base64
import string
import datetime
import time


class Test_GetConsoleOutput(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_GetConsoleOutput, cls).setup_class()
        cls.instance_info_a1 = None
        try:
            cls.instance_info_a1 = create_instances(cls.a1_r1, state='ready')
        except Exception as error:
            try:
                cls.teardown_class()
            except:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.instance_info_a1:
                delete_instances(cls.a1_r1, cls.instance_info_a1)
        finally:
            super(Test_GetConsoleOutput, cls).teardown_class()

    def test_T4362_get_consoleoutput_valid_param(self):
        inst_id = self.instance_info_a1[INSTANCE_ID_LIST][0]
        inst = self.instance_info_a1[INSTANCE_SET][0]
        kp_info = self.instance_info_a1[KEY_PAIR]

        connection = SshTools.check_connection_paramiko(inst['ipAddress'], kp_info[PATH],
                                                        self.a1_r1.config.region.get_info(CENTOS_USER))
        msg_output = id_generator(size=128, chars=string.ascii_letters)
        cmd = "echo " + msg_output + " | sudo tee  /dev/kmsg"
        out, status, error = SshTools.exec_command_paramiko_2(connection, cmd)

        start = datetime.datetime.now()
        while datetime.datetime.now() - start < datetime.timedelta(seconds=300):
            ret = self.a1_r1.fcu.GetConsoleOutput(InstanceId=inst_id)
            if msg_output in base64.b64decode(ret.response.output).decode("utf-8"):
                return
            time.sleep(3)

        assert False, "data not found in console output"
