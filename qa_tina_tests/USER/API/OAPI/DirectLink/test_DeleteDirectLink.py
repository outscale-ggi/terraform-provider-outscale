# -*- coding:utf-8 -*-
import string

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, id_generator
from qa_test_tools.test_base import OscTestSuite


class Test_DeleteDirectLink(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        super(Test_DeleteDirectLink, cls).setup_class()

    def test_T3901_empty_param(self):
        try:
            self.a1_r1.oapi.DeleteDirectLink()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    def test_T3902_invalid_direct_link_id(self):
        try:
            self.a1_r1.oapi.DeleteDirectLink(DirectLinkId='id_invalid')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104', None)
        try:
            self.a1_r1.oapi.DeleteDirectLink(DirectLinkId='dxcon-1234567')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105', None)
        try:
            self.a1_r1.oapi.DeleteDirectLink(DirectLinkId='dxcon-123456789')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105', None)

    def test_T3903_unknown_direct_link_id(self):
        try:
            self.a1_r1.oapi.DeleteDirectLink(DirectLinkId='dxcon-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5072', None)

    @pytest.mark.region_directlink
    def test_T4071_valid_params(self):
        location = self.a1_r1.oapi.ReadLocations().response.Locations[0].Code
        direct_link_name = id_generator(size=8, chars=string.ascii_lowercase)
        ret = self.a1_r1.oapi.CreateDirectLink(DirectLinkName=direct_link_name, Location=location, Bandwidth='1Gbps')
        direct_link_id = ret.response.DirectLink.DirectLinkId
        self.a1_r1.oapi.DeleteDirectLink(DirectLinkId=direct_link_id)

    @pytest.mark.region_directlink
    def test_T4072_with_another_account(self):
        direct_link_id = None
        try:
            location = self.a1_r1.oapi.ReadLocations().response.Locations[0].Code
            direct_link_name = id_generator(size=8, chars=string.ascii_lowercase)
            ret = self.a1_r1.oapi.CreateDirectLink(DirectLinkName=direct_link_name, Location=location, Bandwidth='1Gbps')
            direct_link_id = ret.response.DirectLink.DirectLinkId
            self.a2_r1.oapi.DeleteDirectLink(DirectLinkId=direct_link_id)
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5072', None)
        finally:
            if direct_link_id:
                self.a1_r1.oapi.DeleteDirectLink(DirectLinkId=direct_link_id)
