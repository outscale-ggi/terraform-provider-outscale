
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_oapi_error
from qa_tina_tests.USER.API.OAPI.LoadBalancer.LoadBalancer import LoadBalancer, validate_load_balancer_global_form


class Test_DeleteLoadBalancerPolicy(LoadBalancer):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteLoadBalancerPolicy, cls).setup_class()
        cls.lb_name = None
        cls.setup_error = False
        try:
            cls.lb_name = id_generator(prefix='lbu-')
            cls.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80},
                           {'BackendPort': 1856, 'LoadBalancerProtocol': 'TCP', 'LoadBalancerPort': 1080}],
                LoadBalancerName=cls.lb_name, SubregionNames=[cls.a1_r1.config.region.az_name],
            )
            cls.policy_name_app = id_generator(prefix='policy-')
            cls.a1_r1.oapi.CreateLoadBalancerPolicy(
                LoadBalancerName=cls.lb_name, PolicyName=cls.policy_name_app, PolicyType='app',
                CookieName=id_generator(prefix='cookie-'))
            cls.policy_name_lb = id_generator(prefix='policy-')
            cls.a1_r1.oapi.CreateLoadBalancerPolicy(
                LoadBalancerName=cls.lb_name, PolicyName=cls.policy_name_lb, PolicyType='load_balancer')
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.lb_name:
                try:
                    cls.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=cls.lb_name)
                except:
                    pass
        finally:
            super(Test_DeleteLoadBalancerPolicy, cls).teardown_class()

    def test_T2848_missing_param(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancerPolicy()
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.DeleteLoadBalancerPolicy(LoadBalancerName=self.lb_name)
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.DeleteLoadBalancerPolicy(PolicyName=id_generator(prefix='policy-'))
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2849_unknown_policy(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancerPolicy(LoadBalancerName=self.lb_name, PolicyName=id_generator(prefix='policy-'))
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5056')

    def test_T3551_valid_dry_run(self):
        self.a1_r1.oapi.DeleteLoadBalancerPolicy(LoadBalancerName=self.lb_name, PolicyName=self.policy_name_lb, DryRun=True)

    @pytest.mark.tag_sec_confidentiality
    def test_T3552_with_other_user(self):
        try:
            self.a2_r1.oapi.DeleteLoadBalancerPolicy(LoadBalancerName=self.lb_name, PolicyName=self.policy_name_lb)
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5030')

    def test_T2850_app_policy(self):
        lb = self.a1_r1.oapi.DeleteLoadBalancerPolicy(LoadBalancerName=self.lb_name, PolicyName=self.policy_name_app).response.LoadBalancer
        validate_load_balancer_global_form(lb)

    def test_T2851_lb_policy(self):
        lb = self.a1_r1.oapi.DeleteLoadBalancerPolicy(LoadBalancerName=self.lb_name, PolicyName=self.policy_name_lb).response.LoadBalancer
        validate_load_balancer_global_form(lb)
