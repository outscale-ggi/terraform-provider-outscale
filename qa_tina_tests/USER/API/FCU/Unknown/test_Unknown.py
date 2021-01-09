from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_Unknown(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_Unknown, cls).setup_class()
        cls.conn = cls.a1_r1

    @classmethod
    def teardown_class(cls):
        super(Test_Unknown, cls).teardown_class()

    def test_T1570_without_param(self):
        try:
            self.conn.fcu.DescribeUnknown()
            assert False, "Should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidAction', 'Action is not valid for this web service: DescribeUnknown')

    def test_T1571_with_param(self):
        try:
            self.conn.fcu.DescribeUnknown(Param='foobar')
            assert False, "Should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidAction', 'Action is not valid for this web service: DescribeUnknown')
