from qa_test_tools.test_base import OscTestSuite


class Test_functional(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_functional, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_functional, cls).teardown_class()

    def test_T1400_FCU(self):
        self.a1_r1.fcu.DescribeInstances()

    def test_T1403_EIM(self):
        self.a1_r1.eim.ListAccessKeys()

    def test_T1404_DirectLink(self):
        pass

    def test_T1405_LBU(self):
        self.a1_r1.lbu.DescribeLoadBalancers()

    def test_T1406_ICU(self):
        self.a1_r1.icu.ReadCatalog()
