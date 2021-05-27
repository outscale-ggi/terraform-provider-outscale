
import base64

import pytest

from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import check_tools
from qa_tina_tools.tools.tina.create_tools import create_instances, create_keypair, generate_key
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_keypair, delete_file
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, NAME, PATH, PUBLIC, PRIVATE, \
    INSTANCE_ID_LIST


class Test_keypair(OscTestSuite):

    def exec_import_kp_test(self, key_size):
        kp_info = None
        config = None
        imp = None
        try:
            # create key
            key_name = id_generator(prefix='kp_')
            kp_info = generate_key(key_name, key_size=key_size)
            # import key pair
            file = open(kp_info[PUBLIC])
            public_key_material = file.read()
            imp = self.a1_r1.fcu.ImportKeyPair(KeyName=key_name,
                                               PublicKeyMaterial=base64.b64encode(public_key_material.encode('utf-8')).decode('utf-8'))
            # create instance with key
            config = create_instances(self.a1_r1, key_name=key_name, state='ready')
            ip_address = config[INSTANCE_SET][0]['ipAddress']
            # access instance using key
            check_tools.check_ssh_connection(self.a1_r1, config[INSTANCE_ID_LIST][0], ip_address, kp_info[PRIVATE],
                                             username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        finally:
            if config:
                delete_instances(self.a1_r1, config)
            if kp_info:
                delete_file(kp_info[PUBLIC])
                delete_file(kp_info[PRIVATE])
            if imp:
                self.a1_r1.fcu.DeleteKeyPair(KeyName=key_name)

    def test_T1557_use_created(self):
        kp_info = None
        config = None
        try:
            # create key pair
            kp_info = create_keypair(self.a1_r1)
            # create instance with key
            config = create_instances(self.a1_r1, key_name=kp_info[NAME], state='ready')
            ip_address = config[INSTANCE_SET][0]['ipAddress']
            # access instance using key
            check_tools.check_ssh_connection(self.a1_r1, config[INSTANCE_SET][0]['instanceId'], ip_address, kp_info[PATH],
                                             self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        finally:
            if config:
                delete_instances(self.a1_r1, config)
            if kp_info:
                delete_keypair(self.a1_r1, kp_info)

    @pytest.mark.tag_redwire
    def test_T1558_use_imported(self):
        self.exec_import_kp_test(key_size=2048)

    def test_T3970_use_imported(self):
        self.exec_import_kp_test(key_size=4096)
