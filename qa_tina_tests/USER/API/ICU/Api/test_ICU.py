
from time import sleep
import datetime

import re
import time

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub.osc_api import AuthMethod, EXEC_DATA_METHOD, \
    EXEC_DATA_AUTHENTICATION
import qa_sdk_pub.osc_api as osc_api
from qa_tina_tools.test_base import OscTinaTest
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import known_error

MIN_OVERTIME=4

class Test_ICU(OscTinaTest):

    @pytest.mark.tag_sec_traceability
    def test_T3860_check_request_id(self):
        ret = self.a1_r1.icu.ListAccessKeys()
        assert re.search("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", ret.response.requestId)

    def test_T3861_invalid_call(self):
        try:
            self.a1_r1.icu.foo()
            assert False, 'Call should have been successful'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == "UnknownOperationException"
            assert hasattr(error, 'message')

    def test_T3862_invalid_param(self):
        time.sleep(11)
        self.a1_r1.icu.ListAccessKeys(foo='bar')
        # Invalid para is supported by FCU...

    def test_T3863_method_get(self):
        time.sleep(11)
        try:
            self.a1_r1.icu.ListAccessKeys(exec_data={EXEC_DATA_METHOD: 'GET'})
            assert False, 'Call should have been successful'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == "SerializationException"
            assert hasattr(error, 'message')

    # def test_T3864_check_log(self):
    #    # TODO add test to check log
    #    known_error('PQA-253', 'Add tool to check API logs.')

    @pytest.mark.tag_sec_confidentiality
    def test_T3865_without_authentication(self):
        time.sleep(11)
        try:
            self.a1_r1.icu.ListAccessKeys(exec_data={EXEC_DATA_AUTHENTICATION: AuthMethod.Empty})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == "IcuClientException"
            assert error.message == "Field AuthenticationMethod is required"

    @pytest.mark.tag_sec_confidentiality
    def test_T3866_invalid_authentication(self):
        time.sleep(11)
        sk_bkp = self.a1_r1.config.account.sk
        self.a1_r1.config.account.sk = "foo"
        try:
            self.a1_r1.icu.ListAccessKeys()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert error.status_code == 403
            assert error.error_code == "SignatureDoesNotMatch"
            assert error.message == "The request signature we calculated does not match the signature you provided. " + \
                                    "Check your AWS Secret Access Key and signing method. Consult the service documentation for details."
        finally:
            self.a1_r1.config.account.sk = sk_bkp

    @pytest.mark.tag_sec_availability
    def test_T3867_throttling(self):
        osc_api.disable_throttling()
        nb_ok = 0
        nb_ko = 0
        for _ in range(10):
            try:
                time.sleep(1)
                self.a1_r1.icu.ReadQuotas(max_retry=0)
                nb_ok += 1
            except OscApiException as error:
                if error.status_code == 503:
                    nb_ko += 1
                else:
                    raise
        osc_api.enable_throttling()
        # No throttling on ICU
        assert nb_ok == 10
        assert nb_ko == 0

    def test_T6007_before_date_time_stamp(self):
        try:
            date_time = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
            self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "RequestExpired", None)

        date_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=800)
        date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
        self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})

    def test_T6008_before_date_stamp(self):
        date_time = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp})

        date_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=800)
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp})

    def test_T6009_before_stamps(self):
        try:
            date_time = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
            date_stamp = date_time.strftime('%Y%m%d')
            self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp,
                                                          osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "RequestExpired", None)

        date_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=800)
        date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp,
                                                      osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})

    def test_T6010_incorrect_date_time_stamp(self):
        try:
            date_time_stamp = 'toto'
            self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterValue", None)

    def test_T6011_incorrect_date_stamp(self):
        date_stamp = 'toto'
        self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp})

    def test_T6012_empty_date_time_stamp(self):
        try:
            date_time_stamp = ''
            self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", None)

    def test_T6013_empty_date_stamp(self):
        try:
            date_stamp = ''
            self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 401, 'AuthFailure', None)

    def test_T6014_after_date_time_stamp(self):
        sleep(5)
        try:
            date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=MIN_OVERTIME)
            date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
            ret = self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                                osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            known_error("TINA-6773", "No error raised when sending request with date header in the future")
            assert False, 'Call should not have been successful : {}'.format(ret.response.requestId)
        except OscApiException as error:
            assert False, "remove known error code"
            assert_error(error, 400, "RequestExpired", None)
        sleep(5)
        date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=2)
        date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
        self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                      osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})

    def test_T6015_after_date_stamp(self):
        sleep(5)
        date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=MIN_OVERTIME)
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                      osc_api.EXEC_DATA_DATE_STAMP: date_stamp})
        sleep(5)
        date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=2)
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                      osc_api.EXEC_DATA_DATE_STAMP: date_stamp})

    def test_T6016_after_stamps(self):
        sleep(5)
        try:
            date_time = datetime.datetime.utcnow() + datetime.timedelta(days=MIN_OVERTIME)
            date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
            date_stamp = date_time.strftime('%Y%m%d')
            ret = self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                                osc_api.EXEC_DATA_DATE_STAMP: date_stamp,
                                                                osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            known_error("TINA-6773", "No error raised when sending request with date header in the future")
            assert False, 'Call should not have been successful : {}'.format(ret.response.requestId)
        except OscApiException as error:
            assert False, "remove known error code"
            assert_error(error, 400, "RequestExpired", None)
        sleep(5)
        date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=2)
        date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                      osc_api.EXEC_DATA_DATE_STAMP: date_stamp,
                                                      osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
