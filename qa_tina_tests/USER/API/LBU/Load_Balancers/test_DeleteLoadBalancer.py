from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.wait_tools import wait_load_balancer_state


class Test_DeleteLoadBalancer(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteLoadBalancer, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteLoadBalancer, cls).teardown_class()

    def test_T1251_without_param(self):
        try:
            self.a1_r1.lbu.DeleteLoadBalancer()
            assert False, "Call should not have been successful, request must contain LoadBalancer name"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "The request must contain the parameter LoadBalancerName"

    def test_T49_with_correct_param(self):
        create_load_balancer(self.a1_r1, 'lbu1', listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                             availability_zones=[self.a1_r1.config.region.az_name])
        self.a1_r1.lbu.DeleteLoadBalancer(LoadBalancerName='lbu1')
        wait_load_balancer_state(self.a1_r1, ['lbu1'], True)

    def test_T54_with_invalid_name(self):
        try:
            self.a1_r1.lbu.DeleteLoadBalancer(LoadBalancerName='toto')
        except OscApiException as error:
            assert_error(error, 400, 'LoadBalancerNotFound', "There is no ACTIVE Load Balancer named 'toto'")

    def test_T62_with_incorrect_name(self):
        try:
            self.a1_r1.lbu.DeleteLoadBalancer(LoadBalancerName='lbu_1')
            assert False, "Call should not have been successful, need valid load balancer name"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "Loadbalancer name must contain only alphanumeric characters or hyphens"
