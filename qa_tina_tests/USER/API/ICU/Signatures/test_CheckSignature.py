
import datetime
from time import sleep

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_test_tools.misc import assert_error, generate_signature
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_CheckSignature(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CheckSignature, cls).setup_class()
        try:
            ret = cls.a1_r1.icu.ListAccessKeys()
            cls.ak = ret.response.accessKeys[0]
            cls.kwargs = {
                'StringToSign': 'random_StringToSign',
                'AmzDate': datetime.datetime.utcnow().strftime('%Y%m%d'),
                'Region': 'random_region',
                'ServiceName': 'random_service-name',
                'SecretKey': cls.ak.secretAccessKey
            }
            cls.kwargs['Signature'] = generate_signature(**cls.kwargs)
            cls.kwargs['AccessKeyId'] = cls.ak.accessKeyId
            del cls.kwargs['SecretKey']
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        super(Test_CheckSignature, cls).teardown_class()

    def test_T3764_valid_params(self):
        self.a1_r1.icu.CheckSignature(**self.kwargs)

    def test_T3967_non_authenticated(self):
        self.a1_r1.icu.CheckSignature(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty}, **self.kwargs)

    def test_T3765_incorrect_string(self):
        kwargs = {
            'StringToSign': 'StringToSign',
            'AmzDate': datetime.datetime.utcnow().strftime('%Y%m%d'),
            'Region': 'random_region',
            'ServiceName': 'random_service-name',
            'AccessKeyId': self.ak.accessKeyId,
            'Signature': self.kwargs['Signature']
        }
        try:
            self.a1_r1.icu.CheckSignature(**kwargs)
            assert False, 'Call should not have been successful, incorrect signature'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'SignatureDoesNotMatch'

    def test_T3766_incorrect_date(self):
        kwargs = {
            'StringToSign': 'random_StringToSign',
            # 'AmzDate': datetime.datetime.utcnow().strftime('%Y%m%d'),
            'AmzDate': 'random',
            'Region': 'random_region',
            'ServiceName': 'random_service-name',
            'AccessKeyId': self.ak.accessKeyId,
            'Signature': self.kwargs['Signature']
        }
        try:
            self.a1_r1.icu.CheckSignature(**kwargs)
            assert False, 'Call should not have been successful, incorrect signature'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'SignatureDoesNotMatch'

    def test_T3767_incorrect_region(self):
        kwargs = {
            'StringToSign': 'random_StringToSign',
            'AmzDate': datetime.datetime.utcnow().strftime('%Y%m%d'),
            'Region': 'region',
            'ServiceName': 'random_service-name',
            'AccessKeyId': self.ak.accessKeyId,
            'Signature': self.kwargs['Signature']
        }
        try:
            self.a1_r1.icu.CheckSignature(**kwargs)
            assert False, 'Call should not have been successful, incorrect signature'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'SignatureDoesNotMatch'

    def test_T3768_incorrect_service_name(self):
        kwargs = {
            'StringToSign': 'random_StringToSign',
            'AmzDate': datetime.datetime.utcnow().strftime('%Y%m%d'),
            'Region': 'random_region',
            'ServiceName': 'service-name',
            'AccessKeyId': self.ak.accessKeyId,
            'Signature': self.kwargs['Signature']
        }
        try:
            self.a1_r1.icu.CheckSignature(**kwargs)
            assert False, 'Call should not have been successful, incorrect signature'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'SignatureDoesNotMatch'

    def test_T3769_incorrect_access_key_id(self):
        kwargs = {
            'StringToSign': 'random_StringToSign',
            'AmzDate': datetime.datetime.utcnow().strftime('%Y%m%d'),
            'Region': 'random_region',
            'ServiceName': 'random_service-name',
            'AccessKeyId': self.ak.accessKeyId + 'E',
            'Signature': self.kwargs['Signature']
        }
        try:
            self.a1_r1.icu.CheckSignature(**kwargs)
            assert False, 'Call should not have been successful, incorrect signature'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'SignatureDoesNotMatch'

    def test_T3763_check_throttling(self):
        osc_api.disable_throttling()
        sleep(30)
        self.a1_r1.icu.CheckSignature(**self.kwargs, max_retry=0)
        try:
            self.a1_r1.icu.CheckSignature(**self.kwargs, max_retry=0)
            known_error('TINA-5291', 'Throttling does not function')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert_error(error, 400, '', '')
        finally:
            osc_api.enable_throttling()
        assert False, 'Remove known error code'
