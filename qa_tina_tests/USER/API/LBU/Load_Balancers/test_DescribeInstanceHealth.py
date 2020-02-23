from qa_common_tools.test_base import OscTestSuite


class Test_DescribeInstanceHealth(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeInstanceHealth, cls).setup_class()
        try:
            pass
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_DescribeInstanceHealth, cls).teardown_class()
