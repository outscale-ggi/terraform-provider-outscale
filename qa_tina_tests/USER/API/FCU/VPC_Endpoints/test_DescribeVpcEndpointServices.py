from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.test_base import OscTestSuite, known_error
from qa_common_tools.misc import assert_error, assert_dry_run


class Test_DescribeVpcEndpointServices(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeVpcEndpointServices, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeVpcEndpointServices, cls).teardown_class()

    def test_T4482_valid_dry_run(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpointServices(DryRun=True)
        assert_dry_run(ret)

    def test_T4483_no_params(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpointServices()
        assert ret.response.serviceNameSet

    def test_T4484_with_valid_maxresults(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpointServices(MaxResults=1)
        assert ret.response.serviceNameSet
        ret = self.a1_r1.fcu.DescribeVpcEndpointServices(MaxResults=100)
        assert ret.response.serviceNameSet

    def test_T4485_with_invalid_maxresults(self):
        try:
            self.a1_r1.fcu.DescribeVpcEndpointServices(MaxResults='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Invalid value for parameter 'MaxResults': 'toto'")

    def test_T4486_invalid_next_token_value(self):      
        try:
            self.a1_r1.fcu.DescribeVpcEndpointServices(NextToken=True)
            known_error('TINA-5257', 'DescribeVpcEndpointServices with NextToken attribute')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert_error(error, 400, ' InvalidParameterValue', '')
        try:
            self.a1_r1.fcu.DescribeVpcEndpointServices(NextToken='toto')
            known_error('TINA-5257', 'DescribeVpcEndpointServices with NextToken attribute')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert_error(error, 400, ' InvalidParameterValue', '')
        try:
            self.a1_r1.fcu.DescribeVpcEndpointServices(NextToken=123456789)
            known_error('TINA-5257', 'DescribeVpcEndpointServices with NextToken attribute')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert_error(error, 400, ' InvalidParameterValue', '')
