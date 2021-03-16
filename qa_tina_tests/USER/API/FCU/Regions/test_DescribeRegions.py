
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite

ATTRIBUTES = ['regionName', 'regionEndpoint']


def verify_response(response):
    for reg in response.regionInfo:
        assert hasattr(reg, 'regionName'), "Missing attribute 'regionName' in response"
        assert hasattr(reg, 'regionEndpoint'), "Missing attribute 'regionEndpoint' in response"
    assert len(response.regionInfo) == len({reg.regionName for reg in response.regionInfo}), "Duplicate(s) in region names"
    assert len(response.regionInfo) == len({reg.regionEndpoint for reg in response.regionInfo}), 'Duplicate(s) in region endpoints'


class Test_DescribeRegions(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeRegions, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeRegions, cls).teardown_class()

    def test_T3124_no_params(self):
        ret = self.a1_r1.fcu.DescribeRegions().response
        verify_response(ret)

    def test_T3380_no_authorization(self):
        ret = self.a1_r1.fcu.DescribeRegions(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty}).response
        verify_response(ret)

    # RegionName, Filter --> region-name, endpoint

    def test_T3264_invalid_region_name(self):
        try:
            self.a1_r1.fcu.DescribeRegions(RegionName='eu-west-2')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'NoSuchEntityException')

    def test_T3265_unknown_region_name(self):
        try:
            self.a1_r1.fcu.DescribeRegions(RegionName=['toto'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'NoSuchEntityException')

    def test_T3266_incorrect_filter_key(self):
        try:
            self.a1_r1.fcu.DescribeRegions(Filter=[{'Name': 'toto', 'Value': ['eu-west-2']}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidFilter', 'The filter is invalid: toto')

    def test_T3267_unknown_filter_value(self):
        ret = self.a1_r1.fcu.DescribeRegions(Filter=[{'Name': 'region-name', 'Value': ['toto']}])
        assert not ret.response.regionInfo, 'Unexpected item in result'

    def test_T3268_valid_region_name_filter(self):
        ret = self.a1_r1.fcu.DescribeRegions(Filter=[{'Name': 'region-name', 'Value': ['eu-west-2']}])
        assert not ret.response.regionInfo, 'Unexpected item in result'

    def test_T3269_valid_endpoint_filter(self):
        ret = self.a1_r1.fcu.DescribeRegions(Filter=[{'Name': 'endpoint', 'Value': ['fcu.eu-west-2.outscale.com']}])
        assert not ret.response.regionInfo, 'Unexpected item in result'

    def test_T3270_valid_filters(self):
        ret = self.a1_r1.fcu.DescribeRegions(Filter=[{'Name': 'region-name', 'Value': ['eu-west-2']},
                                                     {'Name': 'endpoint', 'Value': ['fcu.eu-west-2.outscale.com']}])
        assert not ret.response.regionInfo, 'Unexpected item in result'

    def test_T3271_incompatible_filter_values(self):
        ret = self.a1_r1.fcu.DescribeRegions(Filter=[{'Name': 'region-name', 'Value': ['us-east-2']},
                                                     {'Name': 'endpoint', 'Value': ['fcu.eu-west-2.outscale.com']}])
        assert not ret.response.regionInfo, 'Unexpected item in result'
