# -*- coding: utf-8 -*-

import base64

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.info_keys import PUBLIC
from qa_tina_tools.tools.tina.create_tools import generate_key
from qa_tina_tools.tools.tina.delete_tools import delete_key


class Test_ImportKeyPair(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ImportKeyPair, cls).setup_class()
        cls.key_name = id_generator(prefix='kn_')
        cls.kp_info = None
        cls.pk_material = None
        try:
            cls.kp_info = generate_key(cls.key_name)
            file = open(cls.kp_info[PUBLIC])
            cls.pk_material = file.read()
            file.close()
        except Exception:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.kp_info:
                delete_key(cls.kp_info)
        finally:
            super(Test_ImportKeyPair, cls).teardown_class()

    def test_T1591_without_keyname(self):

        try:
            self.a1_r1.fcu.ImportKeyPair(PublicKeyMaterial=base64.b64encode(self.pk_material.encode('utf-8')).decode('utf-8'))
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: Name')

    def test_T1592_without_material(self):
        try:
            self.a1_r1.fcu.ImportKeyPair(KeyName=self.key_name)
            try:
                self.a1_r1.DeleteKeyPair(KeyName=self.key_name)
            except Exception:
                print('Could not delete key pair')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: PublicKeyMaterial')

    def test_T1593_without_param(self):
        try:
            self.a1_r1.fcu.ImportKeyPair()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: PublicKeyMaterial')

    def test_T1594_with_incorrect_keyname(self):
        try:
            name = id_generator(size=10000)
            self.a1_r1.fcu.ImportKeyPair(KeyName=name, PublicKeyMaterial=base64.b64encode(self.pk_material.encode('utf-8')).decode('utf-8'))
            try:
                self.a1_r1.fcu.DeleteKeyPair(KeyName=name)
            except Exception:
                print('Could not delete key pair')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         "Parameter 'KeyName' is invalid: {}. Constraints: Only ASCII characters, max length 255".format(name))

    def test_T1595_with_incorrect_material(self):
        try:
            self.a1_r1.fcu.ImportKeyPair(KeyName=self.key_name, PublicKeyMaterial=base64.b64encode('azerty'.encode('utf-8')).decode('utf-8'))
            try:
                self.a1_r1.DeleteKeyPair(KeyName=self.key_name)
            except Exception:
                print('Could not delete key pair')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidKeyPair.Format', 'Invalid DER encoded key material')

    def test_T1597_with_not_encoded_material(self):
        try:
            self.a1_r1.fcu.ImportKeyPair(KeyName=self.key_name, PublicKeyMaterial="lkhglglkglkhjglkjhglkjhglkjhg")
            try:
                self.a1_r1.fcu.DeleteKeyPair(KeyName=self.key_name)
            except Exception:
                print('Could not delete key pair')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidKeyPair.Format', 'Invalid DER encoded key material')

    def test_T1596_with_correct_params(self):
        # TDODO test various names ...
        ret1 = None
        try:
            ret1 = self.a1_r1.fcu.ImportKeyPair(KeyName=self.key_name,
                                                PublicKeyMaterial=base64.b64encode(self.pk_material.encode('utf-8')).decode('utf-8'))
        except Exception as error:
            raise error
        finally:
            if ret1:
                try:
                    self.a1_r1.fcu.DeleteKeyPair(KeyName=ret1.response.keyName)
                except Exception:
                    print('Could not delete key pair')
