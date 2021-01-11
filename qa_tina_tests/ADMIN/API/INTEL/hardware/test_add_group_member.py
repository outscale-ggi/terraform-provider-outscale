from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_add_group_member(OscTestSuite):

    def test_T4310_invalid_servers(self):
        try:
            self.a1_r1.intel.hardware.add_group_member(group='NVIDIA', servers=['xx'])
        except OscApiException as err:
            assert_error(err, 200, 0, 'no-such-device')

    def test_T4311_invalid_group(self):
        try:
            self.a1_r1.intel.hardware.add_group_member(group='xx', servers=['xx'])
        except OscApiException as err:
            assert_error(err, 200, 0, 'no-such-servergroup')
