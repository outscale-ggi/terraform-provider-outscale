# -*- coding:utf-8 -*-
import random
import string

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import oapi
from qa_tina_tools.tools.tina.create_tools import generate_key
from qa_tina_tools.tina.info_keys import PUBLIC, PRIVATE
from qa_common_tools.ssh import SshTools, KeyType
from cryptography.hazmat.primitives.asymmetric import ec
from qa_tina_tools.tina import info_keys
from qa_test_tools.config import config_constants as constants


class Test_CheckConnectionSsh(OscTestSuite):

    def test_T5112_valid_check_connection_import_ec_key_256(self):
        key_resp = None
        vm_info = None

        keypair_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))

        try:
            key_info = generate_key(keypair_name, key_size=ec.SECP256R1(), crypto_type=KeyType.ecdsa)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(vm_info[info_keys.VMS][0]['PublicIp'], key_info[PRIVATE], key_type=KeyType.ecdsa,username=self.a1_r1.config.region.get_info(
                                                               constants.CENTOS_USER))

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)

    def test_T5113_valid_check_connection_import_ec_key_384(self):
        key_resp = None
        vm_info = None

        keypair_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))

        try:
            key_info = generate_key(keypair_name, key_size=ec.SECP384R1(), crypto_type=KeyType.ecdsa)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(vm_info[info_keys.VMS][0]['PublicIp'], key_info[PRIVATE], key_type=KeyType.ecdsa, username=self.a1_r1.config.region.get_info(
                                                               constants.CENTOS_USER))

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)

    def test_T5114_valid_check_connection_import_ec_key_521(self):
        key_resp = None
        vm_info = None

        keypair_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))

        try:
            key_info = generate_key(keypair_name, key_size=ec.SECP521R1(), crypto_type=KeyType.ecdsa)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(vm_info[info_keys.VMS][0]['PublicIp'], key_info[PRIVATE], key_type=KeyType.ecdsa, username=self.a1_r1.config.region.get_info(
                                                               constants.CENTOS_USER))

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)

    def test_T5111_valid_check_connection_import_ed25519(self):
        key_resp = None
        vm_info = None

        keypair_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))

        try:
            key_info = generate_key(keypair_name, crypto_type=KeyType.ed25519)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(vm_info[info_keys.VMS][0]['PublicIp'], key_info[PRIVATE], key_type=KeyType.ed25519,username=self.a1_r1.config.region.get_info(
                                                               constants.CENTOS_USER))

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)

    def test_T5107_valid_check_connection_rsa_1024(self):
        key_resp = None
        vm_info = None

        keypair_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))

        try:
            key_info = generate_key(keypair_name, crypto_type=KeyType.rsa, key_size=1024)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(vm_info[info_keys.VMS][0]['PublicIp'], key_info[PRIVATE], key_type=KeyType.rsa,username=self.a1_r1.config.region.get_info(
                                                               constants.CENTOS_USER))

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)


    def test_T5109_valid_check_connection_rsa_2048(self):
        key_resp = None
        vm_info = None

        keypair_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))

        try:
            key_info = generate_key(keypair_name, crypto_type=KeyType.rsa, key_size=2048)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(vm_info[info_keys.VMS][0]['PublicIp'], key_info[PRIVATE], key_type=KeyType.rsa,username=self.a1_r1.config.region.get_info(
                                                               constants.CENTOS_USER))

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)

    def test_T5108_valid_check_connection_rsa_3072(self):
        key_resp = None
        vm_info = None

        keypair_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))

        try:
            key_info = generate_key(keypair_name, crypto_type=KeyType.rsa, key_size=3072)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(vm_info[info_keys.VMS][0]['PublicIp'], key_info[PRIVATE], key_type=KeyType.rsa,username=self.a1_r1.config.region.get_info(
                                                               constants.CENTOS_USER))

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)

    def test_T5110_valid_check_connection_rsa_4096(self):
        key_resp = None
        vm_info = None

        keypair_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))

        try:
            key_info = generate_key(keypair_name, crypto_type=KeyType.rsa, key_size=4096)

            with open(key_info[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()

            key_resp = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name, PublicKey=pub_key).response
            vm_info = oapi.create_Vms(self.a1_r1, key_name=keypair_name, state='ready')

            SshTools.check_connection_paramiko(vm_info[info_keys.VMS][0]['PublicIp'], key_info[PRIVATE], key_type=KeyType.rsa,username=self.a1_r1.config.region.get_info(
                                                               constants.CENTOS_USER))

        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if key_resp:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)
