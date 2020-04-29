from qa_test_tools.test_base import OscTestSuite
from qa_sdk_pub.osc_api import disable_throttling
import time
import sys
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.error import group_errors
from qa_sdk_pub import osc_api

# ec2/throttling/Describe* --> 0,5


# FRONT_NUM = 3
FRONT_NUM = 1


class Test_fcu_throttling(OscTestSuite):

    def test_T3990_dist_success(self):
        disable_throttling()
        min_dist_success = sys.maxsize
        max_dist_success = 0
        last_success = 0
        errs = group_errors()
        osc_api.disable_throttling()
        for _ in range(500):
            try:
                self.a1_r1.fcu.DescribeAddresses(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                tmp_time = time.time()
                if last_success:
                    min_dist_success = min(min_dist_success, tmp_time-last_success)
                    max_dist_success = max(max_dist_success, tmp_time-last_success)
                last_success = tmp_time
            except OscApiException as error:
                if hasattr(error, 'status_code') and error.status_code == 503:
                    pass
                else:
                    errs.handle_api_exception(error)
            except OscTestException as error:
                errs.add_unexpected_error(error)
        osc_api.enable_throttling()
        print('min_dist_success = {}'.format(min_dist_success))
        print('max_dist_success = {}'.format(max_dist_success))
        errs.assert_errors()

    def test_T4001_throttling_same_param(self):
        has_throttling_error = False
        osc_api.disable_throttling()
        for _ in range(FRONT_NUM + 1):
            try:
                self.a1_r1.fcu.DescribeAddresses(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
            except OscApiException as error:
                if hasattr(error, 'status_code') and error.status_code == 503:
                    has_throttling_error = True
                    break
        osc_api.enable_throttling()
        assert has_throttling_error, 'Throttling error did not occur'

    def test_T4002_throttling_diff_param(self):
        has_throttling_error = False
        osc_api.disable_throttling()
        for i in range(FRONT_NUM + 1):
            try:
                self.a1_r1.fcu.DescribeAddresses(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0}, PublicIp='192.168.1.{}'.format(i))
            except OscApiException as error:
                if hasattr(error, 'status_code') and error.status_code == 503:
                    has_throttling_error = True
                    break
        osc_api.enable_throttling()
        assert has_throttling_error, 'Throttling error did not occur'
