# -*- coding:utf-8 -*-
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, id_generator
from qa_test_tools.test_base import OscTestSuite
import string
import pytest

from qa_tina_tools.specs.oapi.check_tools import check_oapi_response


@pytest.mark.region_directlink
class Test_CreateDirectLink(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        super(Test_CreateDirectLink, cls).setup_class()
        cls.location = None
        ret = cls.a1_r1.oapi.ReadLocations()
        if ret.response.Locations:
            cls.location = ret.response.Locations[0].Code

    def setup_method(self, method):
        super(Test_CreateDirectLink, self).setup_method(method)
        self.direct_link_id = None

    def teardown_method(self, method):
        try:
            if self.direct_link_id:
                self.a1_r1.oapi.DeleteDirectLink(DirectLinkId=self.direct_link_id)
        except Exception as error:
            raise error
        finally:
            super(Test_CreateDirectLink, self).teardown_method(method)

    def test_T3897_empty_param(self):
        try:
            self.a1_r1.oapi.CreateDirectLink()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    def test_T3898_missing_parameters(self):
        try:
            self.a1_r1.oapi.CreateDirectLink(DirectLinkName='test_name')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        try:
            self.a1_r1.oapi.CreateDirectLink(Location='test_location')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        try:
            self.a1_r1.oapi.CreateDirectLink(Bandwidth='1Gbps')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        try:
            self.a1_r1.oapi.CreateDirectLink(Bandwidth='1Gbps', DirectLinkName='test_name')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        try:
            self.a1_r1.oapi.CreateDirectLink(DirectLinkName='test_name', Location=self.location)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        try:
            self.a1_r1.oapi.CreateDirectLink(Bandwidth='1Gbps', Location='test_location')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    def test_T3899_unknown_location(self):
        try:
            self.a1_r1.oapi.CreateDirectLink(Bandwidth='1Gbps', DirectLinkName='test_name', Location='unknown_location')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5052', None)

    def test_T3900_invalid_bandwidth(self):
        try:
            self.a1_r1.oapi.CreateDirectLink(Bandwidth='alpha1Gbps', DirectLinkName='test_name', Location=self.location)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045', None)
        try:
            self.a1_r1.oapi.CreateDirectLink(Bandwidth='1', DirectLinkName='test_name', Location=self.location)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045', None)

    @pytest.mark.region_directlink
    def test_T4070_valid_params(self):
        direct_link_name = id_generator(size=8, chars=string.ascii_lowercase)
        resp = self.a1_r1.oapi.CreateDirectLink(DirectLinkName=direct_link_name, Location=self.location, Bandwidth='1Gbps').response
        self.direct_link_id = resp.DirectLink.DirectLinkId
        check_oapi_response(resp, 'CreateDirectLinkResponse')
        assert resp.DirectLink.RegionName == self.a1_r1.config.region.name
        assert resp.DirectLink.AccountId == self.a1_r1.config.account.account_id
        assert resp.DirectLink.State == 'pending'
        assert resp.DirectLink.Bandwidth == '1Gbps'
        assert resp.DirectLink.Location == self.location
        assert resp.DirectLink.DirectLinkName == direct_link_name
        assert resp.DirectLink.RegionName == self.a1_r1.config.region.name
