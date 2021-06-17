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
        assert not resp.networkInterfaceSet
