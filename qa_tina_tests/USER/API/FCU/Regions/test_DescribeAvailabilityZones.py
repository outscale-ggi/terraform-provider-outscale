from qa_test_tools.test_base import OscTestSuite
from specs.check_tools import check_response


class Test_DescribeAvailabilityZones(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeAvailabilityZones, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeAvailabilityZones, cls).teardown_class()

    def test_T5664_no_param(self):
        ret = self.a1_r1.fcu.DescribeAvailabilityZones()
        ret.check_response()