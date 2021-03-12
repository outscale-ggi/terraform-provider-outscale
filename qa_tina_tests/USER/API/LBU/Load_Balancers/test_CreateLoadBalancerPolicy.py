

import pytest

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_CreateLoadBalancerPolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateLoadBalancerPolicy, cls).setup_class()
        cls.lbu_name = None
        try:
            name = id_generator('lbu')
            create_load_balancer(cls.a1_r1,
                                 name,
                                 listeners=[{'InstancePort': '80',
                                             'LoadBalancerPort': '80',
                                             'Protocol': 'TCP'}])
            cls.lbu_name = name
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.lbu_name:
                delete_lbu(cls.a1_r1, cls.lbu_name)
        finally:
            super(Test_CreateLoadBalancerPolicy, cls).teardown_class()

    def test_T4452_default_param(self):
        policy_name = id_generator('policy')
        self.a1_r1.lbu.CreateLoadBalancerPolicy(LoadBalancerName=self.lbu_name, PolicyName=policy_name, PolicyTypeName='ProxyProtocolPolicyType')

    def test_T4453_without_load_balancer_name(self):
        policy_name = id_generator('policy')
        try:
            self.a1_r1.lbu.CreateLoadBalancerPolicy(PolicyName=policy_name, PolicyTypeName='ProxyProtocolPolicyType')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerName')

    def test_T4454_without_policy_name(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancerPolicy(LoadBalancerName=self.lbu_name, PolicyTypeName='ProxyProtocolPolicyType')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'The request must contain the parameter PolicyName')

    def test_T4455_without_policy_type_name(self):
        policy_name = id_generator('policy')
        try:
            self.a1_r1.lbu.CreateLoadBalancerPolicy(LoadBalancerName=self.lbu_name, PolicyName=policy_name)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'The request must contain the parameter PolicyTypeName')

    def test_T4456_with_invalid_policy_type_name(self):
        policy_name = id_generator('policy')
        try:
            self.a1_r1.lbu.CreateLoadBalancerPolicy(LoadBalancerName=self.lbu_name, PolicyName=policy_name, PolicyTypeName='foo')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         "Value of parameter 'PolicyTypeName' is not valid: foo. Supported values: ProxyProtocolPolicyType")

    @pytest.mark.tag_sec_confidentiality
    def test_T4457_with_lbu_from_other_account(self):
        policy_name = id_generator('policy')
        try:
            self.a2_r1.lbu.CreateLoadBalancerPolicy(LoadBalancerName=self.lbu_name, PolicyName=policy_name, PolicyTypeName='ProxyProtocolPolicyType')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'LoadBalancerNotFound', "There is no ACTIVE Load Balancer named '{}'".format(self.lbu_name))
