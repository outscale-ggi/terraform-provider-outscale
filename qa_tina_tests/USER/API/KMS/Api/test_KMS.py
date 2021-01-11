# pylint: disable=missing-docstring

import re
import time

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
import qa_sdk_pub.osc_api as osc_api
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite


@pytest.mark.region_kms
class Test_KMS(OscTestSuite):

    @pytest.mark.tag_sec_traceability
    def test_T3881_check_request_id(self):
        ret = self.a1_r1.kms.ListKeys()
        assert re.search("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", ret.response.requestId)

    def test_T3882_invalid_call(self):
        try:
            self.a1_r1.kms.foo()
            assert False, 'Call should have been successful'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == "UnknownOperationException"
            assert hasattr(error, 'message')

    def test_T3883_invalid_param(self):
        self.a1_r1.kms.ListKeys(foo='bar')

    def test_T3884_method_get(self):
        try:
            self.a1_r1.kms.ListKeys(exec_data={osc_api.EXEC_DATA_METHOD: 'GET'})
            assert False, 'Call should have been successful'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == "SerializationException"
            assert hasattr(error, 'message')

    # def test_T3885_check_log(self):
    #    # TODO add test to check log
    #    known_error('PQA-253', 'Add tool to check API logs.')

    @pytest.mark.tag_sec_confidentiality
    def test_T3886_without_authentication(self):
        try:
            self.a1_r1.kms.ListKeys(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 401, "AuthFailure",
                          "Outscale was not able to validate the provided access credentials. Invalid login/password or password has expired.")

    @pytest.mark.tag_sec_confidentiality
    def test_T3887_invalid_authentication(self):
        sk_bkp = self.a1_r1.config.account.sk
        self.a1_r1.config.account.sk = "foo"
        try:
            self.a1_r1.kms.ListKeys()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 403, "SignatureDoesNotMatch", "The request signature we calculated does not match the signature you provided. " + \
                         "Check your AWS Secret Access Key and signing method. Consult the service documentation for details.")
        finally:
            self.a1_r1.config.account.sk = sk_bkp

    @pytest.mark.tag_sec_availability
    def test_T3888_throttling(self):
        osc_api.disable_throttling()
        nb_ok = 0
        nb_ko = 0
        start = time.time()
        for _ in range(10):
            try:
                self.a1_r1.kms.ListKeys(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                nb_ok += 1
            except OscApiException as error:
                if error.status_code == 503:
                    nb_ko += 1
                else:
                    raise
        end = time.time()
        time_check = end - start
        osc_api.enable_throttling()
        assert nb_ok != 0
        assert nb_ko != 0 or time_check > 5
