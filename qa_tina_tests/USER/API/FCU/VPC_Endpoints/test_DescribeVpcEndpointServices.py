from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest


class Test_DescribeVpcEndpointServices(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeVpcEndpointServices, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeVpcEndpointServices, cls).teardown_class()

    def test_T4482_valid_dry_run(self):
        try:
            self.a1_r1.fcu.DescribeVpcEndpointServices(DryRun=True)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'DryRunOperation', 'Request would have succeeded, but DryRun flag is set.')

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
