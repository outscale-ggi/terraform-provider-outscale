
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from specs.check_tools import check_directlink_error
from qa_tina_tools.test_base import OscTinaTest


@pytest.mark.region_directlink
class Test_DescribeVirtualGateways(OscTinaTest):

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
            check_directlink_error(error, 3001)
