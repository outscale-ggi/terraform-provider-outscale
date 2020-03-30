# pylint: disable=missing-docstring

import re
import pytest

import qa_sdk_pub.osc_api as osc_api
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite, known_error
import subprocess
import json
from qa_tina_tools.specs.oapi import OAPI_PATHS
from qa_test_tools.misc import assert_error
import datetime
from qa_test_tools import misc


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
            if error.status_code == 500 and error.message == 'InternalError':
                known_error('GTW-1231', 'ReadVolumes without params and with invalid authentication returns an internal error')
            assert False, 'Remove known error'
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
        batcmd = "curl -X POST https://api.{}.outscale.com/api/V1/ReadPublicIpRanges".format(self.a1_r1.config.region.name)
        batcmd += " -d '{}'"
        result = subprocess.check_output(batcmd, shell=True)
        json_result = json.loads(result)
        assert 'Errors' not in json_result 

    def test_T4772_check_param_encoding(self):
        sg_ids = []
        resp_tags = None
        tag_key = 'key'
        tag_value = '%2Fdev%2Fxvdb'
        try:
            resp = self.a1_r1.oapi.CreateSecurityGroup(SecurityGroupName=misc.id_generator(prefix='sg_name'), Description='desc').response
            sg_ids.append(resp.SecurityGroup.SecurityGroupId)
            resp = self.a1_r1.oapi.CreateSecurityGroup(
                SecurityGroupName=misc.id_generator(prefix='sg_name'),
                Description='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ._-:/()#,@[]+=&;{}!$').response
            sg_ids.append(resp.SecurityGroup.SecurityGroupId)
            
            resp_tags = self.a1_r1.oapi.CreateTags(ResourceIds=sg_ids, Tags=[{'Key': tag_key, 'Value': tag_value}])
            resp_read_tags = self.a1_r1.oapi.ReadTags().response
            for tag in resp_read_tags.Tags:
                if tag.ResourceId in sg_ids and tag.Key == 'key':
                    assert tag.Value == tag_value
        finally:
            if resp_tags:
                self.a1_r1.oapi.DeleteTags(ResourceIds=sg_ids, Tags=[{'Key': tag_key, 'Value': tag_value}])
            for sg_id in sg_ids:
                self.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=sg_id)

    def test_T4782_check_param_encoding_with_get(self):
        sg_ids = []
        resp_tags = None
        tag_key = 'key'
        tag_value = '%2Fdev%2Fxvdb'
        try:
            resp = self.a1_r1.oapi.CreateSecurityGroup(SecurityGroupName=misc.id_generator(prefix='sg_name'), Description='desc').response
            sg_ids.append(resp.SecurityGroup.SecurityGroupId)
            resp = self.a1_r1.oapi.CreateSecurityGroup(
                SecurityGroupName=misc.id_generator(prefix='sg_name'),
                Description='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ._-:/()#,@[]+=&;{}!$').response
            sg_ids.append(resp.SecurityGroup.SecurityGroupId)
            
            resp_tags = self.a1_r1.oapi.CreateTags(method='GET', ResourceIds=sg_ids, Tags=[{'Key': tag_key, 'Value': tag_value}])
            assert False, 'Call should not have been successful'
            resp_read_tags = self.a1_r1.oapi.ReadTags().response
            for tag in resp_read_tags.Tags:
                if tag.ResourceId in sg_ids and tag.Key == 'key':
                    assert tag.Value == tag_value
        except OscApiException as error:
            assert_error(error, 405 , "2", "AccessDenied")
        finally:
            if resp_tags:
                self.a1_r1.oapi.DeleteTags(ResourceIds=sg_ids, Tags=[{'Key': tag_key, 'Value': tag_value}])
            for sg_id in sg_ids:
                self.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=sg_id)
