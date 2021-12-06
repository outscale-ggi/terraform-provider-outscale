
import string

import pytest
from specs import check_oapi_error
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import known_error
from qa_test_tools.misc import id_generator
from qa_tina_tools.test_base import OscTinaTest


class Test_DeleteDirectLink(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        super(Test_DeleteDirectLink, cls).setup_class()

    def test_T3901_empty_param(self):
        try:
            self.a1_r1.oapi.DeleteDirectLink()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T3902_invalid_direct_link_id(self):
        try:
            self.a1_r1.oapi.DeleteDirectLink(DirectLinkId='id_invalid')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='id_invalid', prefixes='dxcon-')
        try:
            self.a1_r1.oapi.DeleteDirectLink(DirectLinkId='dxcon-1234567')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='dxcon-1234567')
        try:
            self.a1_r1.oapi.DeleteDirectLink(DirectLinkId='dxcon-123456789')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='dxcon-123456789')

    def test_T3903_unknown_direct_link_id(self):
        try:
            self.a1_r1.oapi.DeleteDirectLink(DirectLinkId='dxcon-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5072, id='dxcon-12345678')

    @pytest.mark.region_directlink
    def test_T4071_valid_params(self):
        try:
            location = self.a1_r1.oapi.ReadLocations().response.Locations[0].Code
            direct_link_name = id_generator(size=8, chars=string.ascii_lowercase)
            ret = self.a1_r1.oapi.CreateDirectLink(DirectLinkName=direct_link_name, Location=location, Bandwidth='1Gbps')
            if self.a1_r1.config.region.name == 'in-west-2':
                assert False, "remove known error"
            direct_link_id = ret.response.DirectLink.DirectLinkId
            self.a1_r1.oapi.DeleteDirectLink(DirectLinkId=direct_link_id)
        except OscApiException as error:
            if self.a1_r1.config.region.name == 'in-west-2':
                check_oapi_error(error, 10001)
                known_error('OPS-14319', 'no directlink on IN2')
            else:
                raise error

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
            if self.a1_r1.config.region.name == 'in-west-2':
                check_oapi_error(error, 10001)
                known_error('OPS-14319', 'no directlink on IN2')
            else:
                raise error
            check_oapi_error(error, 5072, id=direct_link_id)
        finally:
            if direct_link_id:
                self.a1_r1.oapi.DeleteDirectLink(DirectLinkId=direct_link_id)
