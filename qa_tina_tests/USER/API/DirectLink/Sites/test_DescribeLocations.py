
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.test_base import OscTestSuite


@pytest.mark.region_directlink
class Test_DescribeLocations(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeLocations, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeLocations, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T1907_without_param(self):
        ret = self.a1_r1.directlink.DescribeLocations()
        assert isinstance(ret.response.locations, list)
        assert hasattr(ret.response, 'locations')

    def test_T5736_with_extra_param(self):
        try:
            self.a1_r1.directlink.DescribeLocations(Foo='Bar')
        except OscApiException as error:
            misc.assert_error(error, 400, 'DirectConnectClientException', "Operation doesn't expect any parameters")
