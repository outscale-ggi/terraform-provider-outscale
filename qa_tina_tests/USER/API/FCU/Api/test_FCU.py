

import re
import datetime

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
import qa_sdk_pub.osc_api as osc_api
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest

MIN_OVERTIME = 4


class Test_FCU(OscTinaTest):

    @pytest.mark.tag_sec_traceability
    def test_T3833_check_request_id(self):
        ret = self.a1_r1.fcu.DescribeVolumes()
        assert re.search("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", ret.response.requestId)

    def test_T3834_invalid_call(self):
        try:
            self.a1_r1.fcu.foo()
            assert False, 'Call should have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidAction", "Action is not valid for this web service: foo")

    def test_T3835_invalid_param(self):
        self.a1_r1.fcu.DescribeVolumes(foo='bar')
        # Invalid para is supported by FCU...

    def test_T3836_method_get(self):
        self.a1_r1.fcu.DescribeVolumes(method='GET')

    # def test_T3837_check_log(self):
    #    # TODO add test to check log
    #    known_error('PQA-253', 'Add tool to check API logs.')

    @pytest.mark.tag_sec_confidentiality
    def test_T3838_without_authentication(self):
        try:
            self.a1_r1.fcu.DescribeVolumes(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 401, "AuthFailure", "Outscale was not able to validate the provided access credentials. " + \
                         "Invalid login/password or password has expired.")

    @pytest.mark.tag_sec_confidentiality
    def test_T3839_invalid_authentication(self):
        sk_bkp = self.a1_r1.config.account.sk
        self.a1_r1.config.account.sk = "foo"
        try:
            self.a1_r1.fcu.DescribeVolumes()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 403, "SignatureDoesNotMatch", "The request signature we calculated does not match the signature you provided. " + \
                    "Check your AWS Secret Access Key and signing method. Consult the service documentation for details.")
        finally:
            self.a1_r1.config.account.sk = sk_bkp

    @pytest.mark.tag_sec_availability
    def test_T3841_throttling(self):
        osc_api.disable_throttling()
        nb_ok = 0
        nb_ko = 0
        for _ in range(10):
            try:
                self.a1_r1.fcu.DescribeAddresses(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                nb_ok += 1
            except OscApiException as error:
                if error.status_code == 503:
                    nb_ko += 1
                else:
                    raise
        osc_api.enable_throttling()
        assert nb_ok != 0
        assert nb_ko != 0

    def test_T6027_before_date_time_stamp(self):
        try:
            date_time = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
            self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "RequestExpired", None)

        date_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=800)
        date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
        self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})

    def test_T6028_before_date_stamp(self):
        date_time = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp})

        date_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=800)
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp})

    def test_T6029_before_stamps(self):
        try:
            date_time = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
            date_stamp = date_time.strftime('%Y%m%d')
            self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp,
                                                          osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "RequestExpired", None)

        date_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=800)
        date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp,
                                                      osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})

    def test_T6030_incorrect_date_time_stamp(self):
        try:
            date_time_stamp = 'toto'
            self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterValue", None)

    def test_T6031_incorrect_date_stamp(self):
        date_stamp = 'toto'
        self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp})

    def test_T6032_empty_date_time_stamp(self):
        try:
            date_time_stamp = ''
            self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", None)

    def test_T6033_empty_date_stamp(self):
        try:
            date_stamp = ''
            self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 401, 'AuthFailure', None)

    def test_T6034_after_date_time_stamp(self):
        try:
            date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=MIN_OVERTIME)
            date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
            ret = self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                                osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            known_error("TINA-6773", "No error raised when sending request with date header in the future")
            assert False, 'Call should not have been successful : {}'.format(ret.response.requestId)
        except OscApiException as error:
            assert False, "remove known error code"
            assert_error(error, 400, "RequestExpired", None)

        date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=2)
        date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
        self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                      osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})

    def test_T6035_after_date_stamp(self):
        date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=MIN_OVERTIME)
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                      osc_api.EXEC_DATA_DATE_STAMP: date_stamp})

        date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=2)
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                      osc_api.EXEC_DATA_DATE_STAMP: date_stamp})

    def test_T6036_after_stamps(self):
        try:
            date_time = datetime.datetime.utcnow() + datetime.timedelta(days=MIN_OVERTIME)
            date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
            date_stamp = date_time.strftime('%Y%m%d')
            ret = self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                                osc_api.EXEC_DATA_DATE_STAMP: date_stamp,
                                                                osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            known_error("TINA-6773", "No error raised when sending request with date header in the future")
            assert False, 'Call should not have been successful : {}'.format(ret.response.requestId)
        except OscApiException as error:
            assert False, "remove known error code"
            assert_error(error, 400, "RequestExpired", None)

        date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=2)
        date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.fcu.DescribeSecurityGroups(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                      osc_api.EXEC_DATA_DATE_STAMP: date_stamp,
                                                      osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
