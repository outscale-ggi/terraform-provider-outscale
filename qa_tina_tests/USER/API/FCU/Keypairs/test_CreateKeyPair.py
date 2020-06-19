# -*- coding: utf-8 -*-

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error, get_export_value


class Test_CreateKeyPair(OscTestSuite):

    def test_T930_with_valid_keyname(self):
        ret = self.a1_r1.fcu.CreateKeyPair(KeyName='key')
        assert ret.response.keyName == 'key'
        ret = self.a1_r1.fcu.DeleteKeyPair(KeyName='key')

    def test_T929_without_keyname(self):
        try:
            self.a1_r1.fcu.CreateKeyPair()
            assert False, "Creating key pair without key name should not have succeeded"
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY', default_value=False):
                assert_error(error, 400, 'MissingParameter', None)
                assert not error.message
                known_error('GTW-1356', 'Missing error message')
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: Name')

    def test_T931_with_invalid_keyname(self):
        key_name = id_generator(size=256)
        try:
            self.a1_r1.fcu.CreateKeyPair(KeyName=key_name)
            assert False, "Creating key pair with key name longer than 255 should not have succeeded"
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY', default_value=False):
                assert_error(error, 400, 'InvalidParameterValue', None)
                assert not error.message
                known_error('GTW-1356', 'Missing error message')
            assert_error(error, 400, 'InvalidParameterValue',
                         "Parameter 'KeyName' is invalid: {}. Constraints: Only ASCII characters, max length 255".format(key_name))

    # request not correct, this should be modified in the connector
    def test_T932_with_non_ascii_letters(self):
        key_name = 'èàé'
        ret = None
        try:
            ret = self.a1_r1.fcu.CreateKeyPair(KeyName=key_name)
            if get_export_value('OSC_USE_GATEWAY', default_value=False):
                known_error('GTW-1356', 'Missing error')
            assert False, "Non-ascii code should not be accepted"
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY', default_value=False):
                assert False, 'Remove known error'
            if error.status_code != 400:
                known_error('TINA-5696', '404 or 502 error')
            assert False, 'Remove known error'
            assert_error(error, 400, 'InvalidParameterValue',
                         "Parameter 'KeyName' is invalid: èàé. Constraints: Only ASCII characters, max length 255")
        finally:
            if ret:
                self.a1_r1.fcu.DeleteKeyPair(KeyName=key_name)

    def test_T1828_with_existing_name(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.CreateKeyPair(KeyName='test_T1802')
            self.a1_r1.fcu.CreateKeyPair(KeyName='test_T1802')
            assert False, "Call should not have been successful, key with same name exists"
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY', default_value=False):
                assert_error(error, 409, 'InvalidKeyPair.Duplicate', None)
                assert not error.message
                known_error('GTW-1356', 'Missing error message')
            assert_error(error, 400, 'InvalidKeyPair.Duplicate', 'The key pair already exists: test_T1802')
        finally:
            if ret:
                self.a1_r1.fcu.DeleteKeyPair(KeyName='test_T1802')

    def test_T1944_only_spaces(self):
        key_name = '        '
        ret = None
        try:
            ret = self.a1_r1.fcu.CreateKeyPair(KeyName=key_name)
            if get_export_value('OSC_USE_GATEWAY', default_value=False):
                known_error('GTW-1356', 'Missing error')
            assert False, "Only white space code should not be accepted"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         "Parameter 'KeyName' is invalid:         . Constraints: Only ASCII characters, max length 255")
        finally:
            if ret:
                self.a1_r1.fcu.DeleteKeyPair(KeyName=key_name)

    def test_T1943_all_valid_chars(self):
        ret = None
        key_name = ''.join(chr(i) for i in range(32, 127))
        try:
            ret = self.a1_r1.fcu.CreateKeyPair(KeyName=key_name)
        except Exception as error:
            raise error
        finally:
            if ret:
                try:
                    self.a1_r1.fcu.DeleteKeyPair(KeyName=key_name)
                    assert False, 'Remove known error code'
                except OscApiException as error:
                    if error.error_code == 'InvalidKeyPair.NotFound':
                        known_error('TINA-4509', 'Could not delete created key')
                    raise error

    def test_T1947_some_valid_chars(self):
        ret = None
        key_name = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012345678._-:/()#,@[]+=&;{}!$*"
        try:
            ret = self.a1_r1.fcu.CreateKeyPair(KeyName=key_name)
        except Exception as error:
            raise error
        finally:
            if ret:
                self.a1_r1.fcu.DeleteKeyPair(KeyName=key_name)
