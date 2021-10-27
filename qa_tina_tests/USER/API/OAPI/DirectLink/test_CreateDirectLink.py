
import string

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator
from qa_tina_tools.test_base import OscTinaTest
from specs import check_oapi_error


@pytest.mark.region_directlink
class Test_CreateDirectLink(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        cls.direct_link_id = None
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
            check_oapi_error(error, 7000)

    def test_T3898_missing_parameters(self):
        try:
            self.a1_r1.oapi.CreateDirectLink(DirectLinkName='test_name')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateDirectLink(Location='test_location')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateDirectLink(Bandwidth='1Gbps')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateDirectLink(Bandwidth='1Gbps', DirectLinkName='test_name')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateDirectLink(DirectLinkName='test_name', Location=self.location)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateDirectLink(Bandwidth='1Gbps', Location='test_location')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T3899_unknown_location(self):
        try:
            self.a1_r1.oapi.CreateDirectLink(Bandwidth='1Gbps', DirectLinkName='test_name', Location='unknown_location')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5052)

    def test_T3900_invalid_bandwidth(self):
        try:
            self.a1_r1.oapi.CreateDirectLink(Bandwidth='alpha1Gbps', DirectLinkName='test_name', Location=self.location)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4047)
        try:
            self.a1_r1.oapi.CreateDirectLink(Bandwidth='1', DirectLinkName='test_name', Location=self.location)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4047)

    @pytest.mark.region_directlink
    def test_T4070_valid_params(self):
        direct_link_name = id_generator(size=8, chars=string.ascii_lowercase)
        ret = self.a1_r1.oapi.CreateDirectLink(DirectLinkName=direct_link_name, Location=self.location, Bandwidth='1Gbps')
        self.direct_link_id = ret.response.DirectLink.DirectLinkId
        ret.check_response()
        assert ret.response.DirectLink.RegionName == self.a1_r1.config.region.name
        assert ret.response.DirectLink.AccountId == self.a1_r1.config.account.account_id
        assert ret.response.DirectLink.State == 'pending'
        assert ret.response.DirectLink.Bandwidth == '1Gbps'
        assert ret.response.DirectLink.Location == self.location
        assert ret.response.DirectLink.DirectLinkName == direct_link_name
        assert ret.response.DirectLink.RegionName == self.a1_r1.config.region.name
