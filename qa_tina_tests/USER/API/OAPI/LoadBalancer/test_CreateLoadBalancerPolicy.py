

from qa_sdk_common.exceptions.osc_exceptions import OscApiException,\
    OscSdkException
from specs import check_oapi_error
from qa_test_tools.misc import id_generator
from qa_tina_tests.USER.API.OAPI.LoadBalancer.LoadBalancer import LoadBalancer, validate_load_balancer_global_form
from qa_test_tools.test_base import known_error


class Test_CreateLoadBalancerPolicy(LoadBalancer):

    @classmethod
    def setup_class(cls):
        super(Test_CreateLoadBalancerPolicy, cls).setup_class()
        cls.lb_name = id_generator(prefix='lbu-')
        cls.ret_create_lbu = None
        try:
            cls.ret_create_lbu = cls.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80},
                           {'BackendPort': 1856, 'LoadBalancerProtocol': 'TCP', 'LoadBalancerPort': 1080}],
                LoadBalancerName=cls.lb_name, SubregionNames=[cls.a1_r1.config.region.az_name],
            )
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret_create_lbu:
                try:
                    cls.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=cls.lb_name)
                except:
                    print('Could not delete lbu')
        finally:
            super(Test_CreateLoadBalancerPolicy, cls).teardown_class()

    def test_T2843_missing_param(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerPolicy()
            assert False, "call should not have been successful"
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateLoadBalancerPolicy(LoadBalancerName=self.lb_name)
            assert False, "call should not have been successful"
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateLoadBalancerPolicy(PolicyName=id_generator(prefix='policy-'))
            assert False, "call should not have been successful"
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateLoadBalancerPolicy(PolicyType='app')
            assert False, "call should not have been successful"
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateLoadBalancerPolicy(
                LoadBalancerName=self.lb_name, PolicyName=id_generator(prefix='policy-'), PolicyType='app')
            assert False, "call should not have been successful"
        except OscApiException as error:
            check_oapi_error(error, 3002)
        try:
            self.a1_r1.oapi.CreateLoadBalancerPolicy(
                PolicyName=id_generator(prefix='policy-'), PolicyType='app')
            assert False, "call should not have been successful"
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T2844_invalid_lb_policy_creation(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerPolicy(
                LoadBalancerName=self.lb_name, PolicyName=id_generator(prefix='policy-'), PolicyType='load_balancer',
                CookieName=id_generator(prefix='policy-'))
        except OscApiException as error:
            check_oapi_error(error, 3002)

    def test_T2845_valid_app_policy_creation(self):
        lb = self.a1_r1.oapi.CreateLoadBalancerPolicy(
            LoadBalancerName=self.lb_name, PolicyName=id_generator(prefix='policy-'), PolicyType='app',
            CookieName=id_generator(prefix='cookie-')).response.LoadBalancer
        validate_load_balancer_global_form(lb)

    def test_T2846_valid_lb_policy_creation(self):
        lb = self.a1_r1.oapi.CreateLoadBalancerPolicy(
            LoadBalancerName=self.lb_name, PolicyName=id_generator(prefix='policy-'),
            PolicyType='load_balancer', CookieExpirationPeriod=10).response.LoadBalancer
        assert lb.LoadBalancerStickyCookiePolicies[0].CookieExpirationPeriod == 10
        validate_load_balancer_global_form(lb)

    def test_T2847_invalid_policy_type(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerPolicy(
                LoadBalancerName=self.lb_name, PolicyName=id_generator(prefix='policy-'), PolicyType='invalid')
            assert False, "call should not have been successful"
        except OscApiException as error:
            try:
                check_oapi_error(error, 4128, value='invalid', param_name='PolicyType', supported_value='app, load_balancer')
            except OscSdkException:
                known_error('API-425', 'placeholders not replaced')
            assert False, 'Remove known error code'

    def test_T4677_multi_lbu_same_name_diff_users(self):
        ret_create_lbu = None
        try:
            ret_create_lbu = self.a2_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80},
                           {'BackendPort': 1856, 'LoadBalancerProtocol': 'TCP', 'LoadBalancerPort': 1080}],
                LoadBalancerName=self.lb_name, SubregionNames=[self.a2_r1.config.region.az_name],
            )
            self.a1_r1.oapi.CreateLoadBalancerPolicy(
                LoadBalancerName=self.lb_name, PolicyName=id_generator(prefix='policy-'),
                PolicyType='load_balancer')
        finally:
            if ret_create_lbu:
                try:
                    self.a2_r1.oapi.DeleteLoadBalancer(LoadBalancerName=self.lb_name)
                except:
                    print('Could not delete lbu')

    def test_T5448_invalid_PolicyType_with_special_cr(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerPolicy(LoadBalancerName=self.lb_name, PolicyName=id_generator(prefix='policy-'),
                                                     PolicyType='load_balancé')
            assert False, "call should not have been successful"
        except OscApiException as error:
            try:
                check_oapi_error(error, 4128, value='load_balancé', param_name='PolicyType', supported_value='app, load_balancer')
            except OscSdkException:
                known_error('API-425', 'Case is not respected')
            assert False, 'Remove known error code'
