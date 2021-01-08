# pylint: disable=missing-docstring

import re
import time

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub.osc_api import AuthMethod, EXEC_DATA_METHOD, \
    EXEC_DATA_AUTHENTICATION
import qa_sdk_pub.osc_api as osc_api
from qa_test_tools.test_base import OscTestSuite


class Test_ICU(OscTestSuite):

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
