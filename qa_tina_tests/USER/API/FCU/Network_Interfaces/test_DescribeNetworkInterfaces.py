import os

from qa_test_tools.compare_objects import verify_response
from qa_test_tools.test_base import OscTestSuite


class Test_DescribeNetworkInterfaces(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeNetworkInterfaces, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeNetworkInterfaces, cls).teardown_class()

    def test_T5703_no_param(self):
        resp = self.a1_r1.fcu.DescribeNetworkInterfaces().response
        #verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_empty.json'),
                        #None)
        #add test with ref list empty