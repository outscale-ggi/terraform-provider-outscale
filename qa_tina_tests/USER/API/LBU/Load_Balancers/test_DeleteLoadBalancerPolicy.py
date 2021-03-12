from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_DeleteLoadBalancerPolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteLoadBalancerPolicy, cls).setup_class()
        cls.ret1 = None
        cls.lbu_name = id_generator(prefix='lbu-')
        cls.policy_name = id_generator(prefix='lbu-policy-')
        cls.deleted_policy = False
        try:
            cls.ret1 = create_load_balancer(cls.a1_r1, cls.lbu_name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                            availability_zones=[cls.a1_r1.config.region.az_name])
            cls.a1_r1.lbu.CreateLBCookieStickinessPolicy(LoadBalancerName=cls.lbu_name, PolicyName=cls.policy_name, CookieExpirationPeriod=600)
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret1:
                delete_lbu(cls.a1_r1, cls.lbu_name)
        finally:
            super(Test_DeleteLoadBalancerPolicy, cls).teardown_class()

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        self.deleted_policy = False
        try:
            self.a1_r1.lbu.CreateLBCookieStickinessPolicy(LoadBalancerName=self.lbu_name, PolicyName=self.policy_name, CookieExpirationPeriod=600)
        except:
            try:
                OscTestSuite.teardown_method(self, method)
            except:
                pass
            raise

    def teardown_method(self, method):
        if not self.deleted_policy:
            try:
                self.a1_r1.lbu.DeleteLoadBalancerPolicy(LoadBalancerName=self.lbu_name, PolicyName=self.policy_name)
            finally:
                OscTestSuite.teardown_method(self, method)

    def test_T4017_valid_params(self):
        self.a1_r1.lbu.DeleteLoadBalancerPolicy(LoadBalancerName=self.lbu_name, PolicyName=self.policy_name)
        self.deleted_policy = True

    def test_T4018_without_policy_name(self):
        try:
            self.a1_r1.lbu.DeleteLoadBalancerPolicy(LoadBalancerName=self.lbu_name)
            assert False, "Call souldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", "The request must contain the parameter PolicyName")

    def test_T4019_without_load_balancer_name(self):
        try:
            self.a1_r1.lbu.DeleteLoadBalancerPolicy(PolicyName='policynameforlbu1')
            assert False, "Call souldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", "The request must contain the parameter LoadBalancerName")

    def test_T4020_without_params(self):
        try:
            self.a1_r1.lbu.DeleteLoadBalancerPolicy()
            assert False, "Call souldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", "The request must contain the parameter LoadBalancerName")

    def test_T4021_empty_policy_name(self):
        try:
            self.a1_r1.lbu.DeleteLoadBalancerPolicy(LoadBalancerName=self.lbu_name, PolicyName='')
            assert False, "Call souldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Parameter cannot be empty: PolicyName")

    def test_T4022_empty_loadbalancer_name(self):
        try:
            self.a1_r1.lbu.DeleteLoadBalancerPolicy(LoadBalancerName='', PolicyName=self.policy_name)
            assert False, "Call souldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Parameter cannot be empty: LoadBalancerName")

    def test_T4023_none_policy_name(self):
        try:
            self.a1_r1.lbu.DeleteLoadBalancerPolicy(LoadBalancerName=self.lbu_name, PolicyName=None)
            assert False, "Call souldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", "The request must contain the parameter PolicyName")

    def test_T4024_none_loadbalancer_name(self):
        try:
            self.a1_r1.lbu.DeleteLoadBalancerPolicy(LoadBalancerName=None, PolicyName=self.policy_name)
            assert False, "Call souldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", "The request must contain the parameter LoadBalancerName")

    def test_T4025_non_existent_policy_name(self):
        try:
            self.a1_r1.lbu.DeleteLoadBalancerPolicy(LoadBalancerName=self.lbu_name, PolicyName="XXXXXXX")
            assert False, "Call souldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "PolicyNotFound", "There is no policy with name XXXXXXX for load balancer {}".format(self.lbu_name))

    def test_T4026_non_existent_loadbalancer_name(self):
        try:
            self.a1_r1.lbu.DeleteLoadBalancerPolicy(LoadBalancerName="XXXXX", PolicyName=self.policy_name)
            assert False, "Call souldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "LoadBalancerNotFound", "There is no ACTIVE Load Balancer named 'XXXXX'")

    def test_T4027_with_another_account(self):
        try:
            self.a2_r1.lbu.DeleteLoadBalancerPolicy(LoadBalancerName=self.lbu_name, PolicyName=self.policy_name)
            assert False, "Call souldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "LoadBalancerNotFound", "There is no ACTIVE Load Balancer named '{}'".format(self.lbu_name))
