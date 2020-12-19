import pytest

from qa_test_tools.config import config_constants as constants

from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_images
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import stop_instances, delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, KEY_PAIR, PATH, INSTANCE_ID_LIST
from qa_common_tools.ssh import SshTools
from qa_tina_tools.tools.tina.wait_tools import wait_images_state
from qa_tina_tools.tina import check_tools


class Test_create_and_use_images(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create_and_use_images, cls).setup_class()

        cls.info = None

        try:

            cls.info = create_instances(cls.a1_r1, state='running')
            stop_instances(cls.a1_r1, cls.info[INSTANCE_ID_LIST], force=True, wait=True)

        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:

            delete_instances(cls.a1_r1, cls.info)

        finally:
            super(Test_create_and_use_images, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T64_create_use_image(self):
        image_id = None
        info = None
        try:

            ret = self.a1_r1.fcu.CreateImage(InstanceId=self.info[INSTANCE_ID_LIST][0], Name=id_generator(prefix='omi_'), NoReboot=True)
            image_id = ret.response.imageId

            wait_images_state(osc_sdk=self.a1_r1, image_id_list=[image_id], state='available')

            info = create_instances(self.a1_r1, omi_id=image_id, state='ready')
            public_ip_inst = info[INSTANCE_SET][0]['ipAddress']

            sshclient = check_tools.check_ssh_connection(self.a1_r1, info[INSTANCE_ID_LIST][0], public_ip_inst, info[KEY_PAIR][PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # sshclient = SshTools.check_connection_paramiko(public_ip_inst, info[KEY_PAIR][PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            out, status, _ = SshTools.exec_command_paramiko(sshclient, 'pwd')
            self.logger.info(out)
            assert not status, "SSH command was not executed correctly on the remote host"

        finally:
            if info:
                try:
                    delete_instances(self.a1_r1, info)
                except:
                    pass
            if image_id:
                try:
                    cleanup_images(self.a1_r1, image_id_list=[image_id], force=True)
                except:
                    pass
