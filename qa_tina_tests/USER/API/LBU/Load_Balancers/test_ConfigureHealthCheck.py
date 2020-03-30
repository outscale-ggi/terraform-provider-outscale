import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_ConfigureHealthCheck(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ConfigureHealthCheck, cls).setup_class()
        cls.lbu_name = id_generator('lbu-')
        try:
            create_load_balancer(cls.a1_r1, lb_name=cls.lbu_name, availability_zones=[cls.a1_r1.config.region.az_name],
                                 listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}])
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            delete_lbu(cls.a1_r1, cls.lbu_name)
        finally:
            super(Test_ConfigureHealthCheck, cls).teardown_class()

    def test_T586_with_too_small_healthy_threshold(self):
        try:
            self.a1_r1.lbu.ConfigureHealthCheck(
                LoadBalancerName=self.lbu_name,
                HealthCheck={'HealthyThreshold': 1, 'Interval': 10, 'Target': 'TCP:5000', 'Timeout': 5, 'UnhealthyThreshold': 5})
            pytest.fail("Call should have failed as HealthyThreshold has value too small.")
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", 'Invalid healthy checks count, count must be between 2 and 10')

    def test_T590_with_too_big_healthy_threshold(self):
        try:
            self.a1_r1.lbu.ConfigureHealthCheck(
                LoadBalancerName=self.lbu_name,
                HealthCheck={'HealthyThreshold': 11, 'Interval': 10, 'Target': 'TCP:5000', 'Timeout': 5, 'UnhealthyThreshold': 5})
            pytest.fail("Call should have failed as HealthyThreshold has value too big.")
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", 'Invalid healthy checks count, count must be between 2 and 10')

    def test_T591_with_too_small_unhealthy_threshold(self):
        try:
            self.a1_r1.lbu.ConfigureHealthCheck(
                LoadBalancerName=self.lbu_name,
                HealthCheck={'HealthyThreshold': 5, 'Interval': 10, 'Target': 'TCP:5000', 'Timeout': 5, 'UnhealthyThreshold': 1})
            pytest.fail("Call should have failed as UnhealthyThreshold has value too small.")
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", 'Invalid unhealthy checks count, count must be between 2 and 10')

    def test_T592_with_too_big_unhealthy_threshold(self):
        try:
            self.a1_r1.lbu.ConfigureHealthCheck(
                LoadBalancerName=self.lbu_name,
                HealthCheck={'HealthyThreshold': 5, 'Interval': 10, 'Target': 'TCP:5000', 'Timeout': 5, 'UnhealthyThreshold': 11})
            pytest.fail("Call should have failed as UnhealthyThreshold has value too big.")
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", 'Invalid unhealthy checks count, count must be between 2 and 10')

    def test_T1598_with_timeout_greater_than_interval(self):
        try:
            self.a1_r1.lbu.ConfigureHealthCheck(
                LoadBalancerName=self.lbu_name,
                HealthCheck={'HealthyThreshold': 5, 'Interval': 10, 'Target': 'TCP:5000', 'Timeout': 20, 'UnhealthyThreshold': 5})
            pytest.fail("Call should have failed as Timeout greater than Interval.")
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", 'Interval must be greater than timeout')

    def test_T4138_valid_params(self):
        self.a1_r1.lbu.ConfigureHealthCheck(
            LoadBalancerName=self.lbu_name,
            HealthCheck={'HealthyThreshold': 5, 'Interval': 10, 'Target': 'HTTP:80', 'Timeout': 5, 'UnhealthyThreshold': 5})
        self.a1_r1.lbu.ConfigureHealthCheck(
            LoadBalancerName=self.lbu_name,
            HealthCheck={'HealthyThreshold': 5, 'Interval': 10, 'Target': 'HTTP:80/', 'Timeout': 5, 'UnhealthyThreshold': 5})
        self.a1_r1.lbu.ConfigureHealthCheck(
            LoadBalancerName=self.lbu_name,
            HealthCheck={'HealthyThreshold': 2, 'Interval': 5, 'Target': 'HTTP:80', 'Timeout': 2, 'UnhealthyThreshold': 2})
        self.a1_r1.lbu.ConfigureHealthCheck(
            LoadBalancerName=self.lbu_name,
            HealthCheck={'HealthyThreshold': 10, 'Interval': 600, 'Target': 'HTTP:80', 'Timeout': 10, 'UnhealthyThreshold': 10})
