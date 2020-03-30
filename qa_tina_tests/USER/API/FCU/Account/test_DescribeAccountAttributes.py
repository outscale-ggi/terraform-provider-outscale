from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_DescribeAccountAttributes(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeAccountAttributes, cls).setup_class()
        cls.conn = cls.a1_r1

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeAccountAttributes, cls).teardown_class()

    def test_T1569_without_param(self):
        try:
            self.conn.fcu.DescribeAccountAttributes()
            assert False, "Should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', 'This feature is not yet implemented')
