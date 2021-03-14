

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.misc import assert_oapi_error, id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.info_keys import PUBLIC
from qa_tina_tools.tools.tina.create_tools import generate_key


class Test_CreateKeypair(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateKeypair, cls).setup_class()
        cls.keypair_name = None

    def test_T2344_empty_param(self):
        try:
            self.a1_r1.oapi.CreateKeypair()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2345_invalid_character_name(self):
        try:
            self.a1_r1.oapi.CreateKeypair(KeyName='èàé')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T2346_space_character_name(self):
        try:
            self.a1_r1.oapi.CreateKeypair(KeyName='        ')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T2347_invalid_length_name(self):
        keypair_name = id_generator(prefix='keypair_', size=256)
        try:
            self.a1_r1.oapi.CreateKeypair(KeyName=keypair_name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T2348_valid_name(self):
        ret = None
        try:
            self.keypair_name = id_generator(prefix='keypair_')
            ret = self.a1_r1.oapi.CreateKeypair(KeypairName=self.keypair_name).response.Keypair
            assert ret.KeypairName == self.keypair_name
            assert ret.KeypairFingerprint is not None
            assert ret.PrivateKey is not None
        except OscTestException as err:
            raise err
        finally:
            if ret:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=self.keypair_name)

    def test_T2349_invalid_duplicate_name(self):
        ret = None
        try:
            self.keypair_name = id_generator(prefix='keypair_')
            ret = self.a1_r1.oapi.CreateKeypair(KeypairName=self.keypair_name).response.Keypair
            assert ret.KeypairName == self.keypair_name
            assert ret.KeypairFingerprint is not None
            assert ret.PrivateKey is not None
            try:
                self.a1_r1.oapi.CreateKeypair(KeypairName=self.keypair_name)
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 409, 'ResourceConflict', '9011')
        finally:
            if ret:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=self.keypair_name)

    def test_T2354_invalid_public_key(self):
        self.keypair_name = None
        try:
            self.keypair_name = id_generator(prefix='keypair_')
            self.a1_r1.oapi.CreateKeypair(KeypairName=self.keypair_name, PublicKey='publicKey')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4032')

    def test_T2355_valid_import(self):
        ret = None
        try:
            self.keypair_name = id_generator(prefix='keypair_')
            generated_key = generate_key(self.keypair_name)
            with open(generated_key[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()
            ret = self.a1_r1.oapi.CreateKeypair(KeypairName=self.keypair_name, PublicKey=pub_key).response.Keypair
            assert ret.KeypairName == self.keypair_name
            assert ret.KeypairFingerprint is not None
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4032')
            assert False, 'It\'s a regression'
        finally:
            if ret:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=self.keypair_name)

    def test_T2356_invalid_duplicate_name(self):
        ret = None
        try:
            self.keypair_name = id_generator(prefix='keypair_')
            generated_key = generate_key(self.keypair_name)
            with open(generated_key[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()
            ret = self.a1_r1.oapi.CreateKeypair(KeypairName=self.keypair_name, PublicKey=pub_key).response.Keypair
            assert ret.KeypairName == self.keypair_name
            assert ret.KeypairFingerprint is not None
            try:
                self.a1_r1.oapi.CreateKeypair(KeypairName=self.keypair_name, PublicKey=pub_key)
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 409, 'ResourceConflict', '9011')

        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4032')
            assert False, 'It\'s a regression'
        finally:
            if ret:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=self.keypair_name)

    def test_T5536_name_with_spaces(self):
        ret = None
        try:
            keypair_name = id_generator(prefix='keypair_')
            keypair_name = '   {}   '.format(keypair_name)
            ret = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name).response.Keypair
            assert ret.KeypairName == keypair_name
        finally:
            if ret:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)

    def test_T5537_name_with_plus(self):
        ret = None
        try:
            keypair_name = id_generator(prefix='keypair_')
            keypair_name = '+++{}+++'.format(keypair_name)
            ret = self.a1_r1.oapi.CreateKeypair(KeypairName=keypair_name).response.Keypair
            assert ret.KeypairName == keypair_name
        finally:
            if ret:
                self.a1_r1.oapi.DeleteKeypair(KeypairName=keypair_name)
