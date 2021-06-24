
import pytest

from qa_test_tools import misc
from qa_test_tools.test_base import OscTestSuite
from qa_sdk_common.exceptions.osc_exceptions import OscApiException


@pytest.mark.region_directlink
class Test_DescribeVirtualGateways(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeVirtualGateways, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeVirtualGateways, cls).teardown_class()

    def test_T1912_without_param(self):
        ret = self.a1_r1.directlink.DescribeVirtualGateways()
        assert isinstance(ret.response.virtualGateways, list)
        assert not ret.response.virtualGateways

    def test_T5741_with_extra_param(self):
        try:
            self.a1_r1.directlink.DescribeVirtualGateways(Foo='Bar')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, 'DirectConnectClientException', "Operation doesn't expect any parameters")
