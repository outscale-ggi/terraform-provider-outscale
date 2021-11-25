
import os

from cryptography.hazmat.primitives.asymmetric import ec

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from specs import check_oapi_error
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import info_keys, oapi
from qa_tina_tools.tina.info_keys import PRIVATE, PUBLIC
from qa_tina_tools.tools.tina.create_tools import generate_ed25519_key, generate_key


from qa_common_tools.ssh import KeyType, OscSshError, SshTools  # isort:skip


class Test_CheckConnection(OscTinaTest):
    def test_T5112_valid_check_connection_import_ec_key_256(self):
        key_resp = None
        vm_info = None

        keypair_name = id_generator(size=7)

        try:
            key_info = generate_key(keypair_name, key_size=ec.SECP256R1(), crypto_type=KeyType.ecdsa)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(
                vm_info[info_keys.VMS][0]['PublicIp'],
                key_info[PRIVATE],
                retry=3,
                key_type=KeyType.ecdsa,
                username=self.a1_r1.config.region.get_info(constants.CENTOS_USER),
            )

            assert False, 'Remove the known error code'

        except OscSshError:
            known_error('OMI-127', "Can't reach instances created using ecdsa(256, 384, 521) and ed25519 keys")

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)
                os.remove(key_info[PUBLIC])
                os.remove(key_info[PRIVATE])

    def test_T5113_valid_check_connection_import_ec_key_384(self):
        key_resp = None
        vm_info = None

        keypair_name = id_generator(size=7)

        try:
            key_info = generate_key(keypair_name, key_size=ec.SECP384R1(), crypto_type=KeyType.ecdsa)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(
                vm_info[info_keys.VMS][0]['PublicIp'],
                key_info[PRIVATE],
                retry=3,
                key_type=KeyType.ecdsa,
                username=self.a1_r1.config.region.get_info(constants.CENTOS_USER),
            )

            assert False, 'Remove the known error code'

        except OscSshError:
            known_error('OMI-127', "Can't reach instances created using ecdsa(256, 384, 521) and ed25519 keys")

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)
                os.remove(key_info[PUBLIC])
                os.remove(key_info[PRIVATE])

    def test_T5114_valid_check_connection_import_ec_key_521(self):
        key_resp = None
        vm_info = None

        keypair_name = id_generator(size=7)

        try:
            key_info = generate_key(keypair_name, key_size=ec.SECP521R1(), crypto_type=KeyType.ecdsa)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(
                vm_info[info_keys.VMS][0]['PublicIp'],
                key_info[PRIVATE],
                retry=3,
                key_type=KeyType.ecdsa,
                username=self.a1_r1.config.region.get_info(constants.CENTOS_USER),
            )

            assert False, 'Remove the known error code'

        except OscSshError:
            known_error('OMI-127', "Can't reach instances created using ecdsa(256, 384, 521) and ed25519 keys")

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)
                os.remove(key_info[PUBLIC])
                os.remove(key_info[PRIVATE])

    def test_T5111_valid_check_connection_import_ed25519(self):
        key_resp = None
        vm_info = None

        keypair_name = id_generator(size=7)

        try:
            key_info = generate_ed25519_key(keypair_name)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(
                vm_info[info_keys.VMS][0]['PublicIp'],
                key_info[PRIVATE],
                retry=3,
                key_type=KeyType.ed25519,
                username=self.a1_r1.config.region.get_info(constants.CENTOS_USER),
            )

            assert False, 'Remove the known error code'

        except OscSshError:
            known_error('OMI-127', "Can't reach instances created using ecdsa(256, 384, 521) and ed25519 keys")

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)
                os.remove(key_info[PUBLIC])
                os.remove(key_info[PRIVATE])

    def test_T5107_valid_check_connection_rsa_1024(self):
        key_resp = None
        vm_info = None

        keypair_name = id_generator(size=7)

        try:
            key_info = generate_key(keypair_name, key_size=1024)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(
                vm_info[info_keys.VMS][0]['PublicIp'],
                key_info[PRIVATE],
                retry=10,
                key_type=KeyType.rsa,
                username=self.a1_r1.config.region.get_info(constants.CENTOS_USER),
            )

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)
                os.remove(key_info[PUBLIC])
                os.remove(key_info[PRIVATE])

    def test_T5109_valid_check_connection_rsa_2048(self):
        key_resp = None
        vm_info = None

        keypair_name = id_generator(size=7)

        try:
            key_info = generate_key(keypair_name)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(
                vm_info[info_keys.VMS][0]['PublicIp'],
                key_info[PRIVATE],
                retry=10,
                key_type=KeyType.rsa,
                username=self.a1_r1.config.region.get_info(constants.CENTOS_USER),
            )

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)
                os.remove(key_info[PUBLIC])
                os.remove(key_info[PRIVATE])

    def test_T5108_valid_check_connection_rsa_3072(self):
        key_resp = None
        vm_info = None

        keypair_name = id_generator(size=7)

        try:
            key_info = generate_key(keypair_name, key_size=3072)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(
                vm_info[info_keys.VMS][0]['PublicIp'],
                key_info[PRIVATE],
                retry=10,
                key_type=KeyType.rsa,
                username=self.a1_r1.config.region.get_info(constants.CENTOS_USER),
            )

        except OscApiException as error:
            check_oapi_error(error, 4033)

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)
                os.remove(key_info[PUBLIC])
                os.remove(key_info[PRIVATE])

    def test_T5110_valid_check_connection_rsa_4096(self):

        key_resp = None
        vm_info = None

        keypair_name = id_generator(size=7)

        try:
            key_info = generate_key(keypair_name, key_size=4096)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(
                vm_info[info_keys.VMS][0]['PublicIp'],
                key_info[PRIVATE],
                retry=10,
                key_type=KeyType.rsa,
                username=self.a1_r1.config.region.get_info(constants.CENTOS_USER),
            )

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)
                os.remove(key_info[PUBLIC])
                os.remove(key_info[PRIVATE])
