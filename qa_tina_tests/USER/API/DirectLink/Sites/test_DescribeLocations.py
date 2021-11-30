
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.test_base import OscTinaTest
from specs.check_tools import check_directlink_error


@pytest.mark.region_directlink
class Test_DescribeLocations(OscTinaTest):

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
            check_directlink_error(error, 3001)
