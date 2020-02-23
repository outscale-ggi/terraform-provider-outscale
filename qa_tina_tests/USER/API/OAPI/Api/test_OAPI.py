# pylint: disable=missing-docstring

import re
import pytest

import osc_sdk_pub.osc_api as osc_api
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.test_base import OscTestSuite, known_error
import subprocess
import json
from qa_tina_tools.specs.oapi import OAPI_PATHS
from qa_common_tools.misc import assert_error
import datetime


class Test_OAPI(OscTestSuite):

    @pytest.mark.tag_sec_traceability
    def test_T2221_check_request_id(self):
        ret = self.a1_r1.oapi.ReadVolumes()
        assert re.search("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", ret.response.ResponseContext.RequestId)

    def test_T2222_invalid_call(self):
        try:
            self.a1_r1.oapi.foo()
            assert False, 'Call should have been successful'
        except OscApiException as error:
            assert_error(error, 404, "12000", "InvalidAction")

    def test_T2223_invalid_param(self):
        try:
            self.a1_r1.oapi.ReadVolumes(foo='bar')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "3001", "InvalidParameter")

    def test_T2224_method_get(self):
        try:
            self.a1_r1.oapi.ReadVolumes(method='GET')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 405 , "2", "AccessDenied")

    # @pytest.mark.tag_sec_traceability
    # def test_T2225_check_log(self):
    #    # TODO add test to check log
    #    known_error('PQA-253', 'Add tool to check API logs.')

    @pytest.mark.tag_sec_confidentiality
    def test_T2226_without_authentication(self):
        try:
            self.a1_r1.oapi.ReadVolumes(authentication=False)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 401, "1", "AccessDenied")

    @pytest.mark.tag_sec_confidentiality
    def test_T2227_invalid_authentication(self):
        sk_bkp = self.a1_r1.config.sk
        self.a1_r1.config.sk = "foo"
        try:
            self.a1_r1.oapi.ReadVolumes()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 401, "1", "AccessDenied")
        finally:
            self.a1_r1.config.sk = sk_bkp

    def test_T2228_check_no_aws_references(self):
        # TODO: To be defined
        # known_error('', 'Remove all AWS references in OAPI requests')
        pass

    @pytest.mark.tag_sec_availability
    def test_T2229_throttling(self):
        osc_api.disable_throttling()
        nb_ok = 0
        nb_ko = 0
        start = datetime.datetime.now()
        for _ in range(100):
            try:
                self.a1_r1.oapi.ReadDhcpOptions(DryRun=True, max_retry=0)
                nb_ok += 1
            except OscApiException as error:
                if error.status_code == 401:  # hack
                    pass
                elif error.status_code == 503:
                    nb_ko += 1
                else:
                    raise
        print('Sent 100 messages in {}'.format(datetime.datetime.now() - start))
        print('OK --> {} -- KO --> {}'.format(nb_ok, nb_ko))
        osc_api.enable_throttling()
        assert nb_ok != 0
        assert nb_ko != 0

    def test_T3749_check_aws_signature(self):
        self.a1_r1.oapi.ReadVolumes(sign='AWS')

    def test_T4170_check_oapi_features(self):
        batcmd = "curl -X POST https://api.{}.outscale.com/api".format(self.a1_r1.config.region.name)
        result = subprocess.check_output(batcmd, shell=True)
        result1 = json.loads(result)
        assert 'Versions' in result1
        batcmd += '/' + result1['Versions'][0]
        result = subprocess.check_output(batcmd, shell=True)
        result2 = json.loads(result)
        assert 'Version' in result2 and result1['Versions'][0] == "v" + result2['Version'][0]
        assert len(OAPI_PATHS) == len(result2['Calls'])
        for call in result2['Calls']:
            assert '/' + call in OAPI_PATHS

    def test_T4688_check_oapi_including_version(self):
        batcmd = "curl -X POST https://api.{}.outscale.com/api/V0/ReadPublicIpRanges".format(self.a1_r1.config.region.name)
        batcmd += " -d '{}'"
        result = subprocess.check_output(batcmd, shell=True)
        json_result = json.loads(result)
        assert 'Errors' not in json_result 
