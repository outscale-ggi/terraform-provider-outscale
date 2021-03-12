
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_oapi_error
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu
from qa_tina_tests.USER.API.OAPI.LoadBalancer.LoadBalancer import LoadBalancer


class Test_DeleteLoadBalancer(LoadBalancer):
    lb_name = None

    @classmethod
    def setup_class(cls):
        cls.quotas = {'lb_limit': 10}
        super(Test_DeleteLoadBalancer, cls).setup_class()

    def setup_method(self, method):
        super(Test_DeleteLoadBalancer, self).setup_method(method)
        self.lb_name = None
        try:
            self.lb_name = id_generator(prefix='lbu-')
            create_load_balancer(self.a1_r1, self.lb_name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                 availability_zones=[self.a1_r1.config.region.az_name])
        except:
            try:
                self.teardown_method(method)
            finally:
                raise

    def teardown_method(self, method):
        try:
            if self.lb_name:
                try:
                    delete_lbu(self.a1_r1, lbu_name=self.lb_name)
                except:
                    print('Could not delete lbu')
        finally:
            super(Test_DeleteLoadBalancer, self).teardown_method(method)

    def test_T2603_empty_param(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancer()
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    def test_T2604_unknown_name(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName='tata')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5030')

    def test_T2605_valid_param(self):
        self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=self.lb_name)
        self.lb_name = None

    def test_T3547_valid_dry_run(self):
        self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=self.lb_name, DryRun=True)

    @pytest.mark.tag_sec_confidentiality
    def test_T3548_with_other_user(self):
        try:
            self.a2_r1.oapi.DeleteLoadBalancer(LoadBalancerName=self.lb_name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5030', None)
