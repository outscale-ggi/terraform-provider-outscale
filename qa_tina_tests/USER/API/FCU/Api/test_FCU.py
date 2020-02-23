# pylint: disable=missing-docstring

import re
import pytest

import osc_sdk_pub.osc_api as osc_api
from osc_sdk_pub.osc_api import AuthMethod
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.misc import assert_error


class Test_FCU(OscTestSuite):

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
            self.a1_r1.fcu.DescribeVolumes(auth=AuthMethod.Empty)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 401, "AuthFailure", "Outscale was not able to validate the provided access credentials. Invalid login/password or password has expired.")

    @pytest.mark.tag_sec_confidentiality
    def test_T3839_invalid_authentication(self):
        sk_bkp = self.a1_r1.config.sk
        self.a1_r1.config.sk = "foo"
        try:
            self.a1_r1.fcu.DescribeVolumes()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 403, "SignatureDoesNotMatch", "The request signature we calculated does not match the signature you provided. " + \
                    "Check your AWS Secret Access Key and signing method. Consult the service documentation for details.")
        finally:
            self.a1_r1.config.sk = sk_bkp

    @pytest.mark.tag_sec_availability
    def test_T3841_throttling(self):
        osc_api.disable_throttling()
        nb_ok = 0
        nb_ko = 0
        for _ in range(10):
            try:
                ret = self.a1_r1.fcu.DescribeAddresses(max_retry=0)
                nb_ok += 1
            except OscApiException as error:
                if error.status_code == 503:
                    nb_ko += 1
                else:
                    raise
        osc_api.enable_throttling()
        assert nb_ok != 0
        assert nb_ko != 0
