# pylint: disable=missing-docstring

import pytest

from osc_common.exceptions import OscApiException
from qa_common_tools.misc import id_generator, assert_error
from qa_common_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_SetLoadBalancerPoliciesForBackendServer(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_SetLoadBalancerPoliciesForBackendServer, cls).setup_class()
        cls.lbu_name = None
        cls.policy_name = id_generator('policy')
        try:
            name = id_generator('lbu')
            create_load_balancer(cls.a1_r1,
                                 name,
                                 listeners=[{'InstancePort': '80',
                                             'LoadBalancerPort': '80',
                                             'Protocol': 'TCP'},
                                 {'InstancePort': '100',
                                             'LoadBalancerPort': '100',
                                             'Protocol': 'TCP'}])
            cls.lbu_name = name
            cls.a1_r1.lbu.CreateLoadBalancerPolicy(LoadBalancerName=cls.lbu_name, PolicyName=cls.policy_name,
                                                   PolicyTypeName='ProxyProtocolPolicyType')
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
            super(Test_SetLoadBalancerPoliciesForBackendServer, cls).teardown_class()

    def test_T4458_default_param(self):
        self.a1_r1.lbu.SetLoadBalancerPoliciesForBackendServer(LoadBalancerName=self.lbu_name, PolicyNames=[self.policy_name], InstancePort=80)

    def test_T4687_shared_policy(self):
        self.a1_r1.lbu.SetLoadBalancerPoliciesForBackendServer(LoadBalancerName=self.lbu_name, PolicyNames=[self.policy_name], InstancePort=80)
        self.a1_r1.lbu.SetLoadBalancerPoliciesForBackendServer(LoadBalancerName=self.lbu_name, PolicyNames=[self.policy_name], InstancePort=100)
        ret = self.a1_r1.lbu.DescribeLoadBalancers(LoadBalancerNames=[self.lbu_name])
        assert len(ret.response.DescribeLoadBalancersResult.LoadBalancerDescriptions[0].ListenerDescriptions) == 2

    def test_T4459_without_load_balancer_name(self):
        try:
            self.a1_r1.lbu.SetLoadBalancerPoliciesForBackendServer(PolicyNames=[self.policy_name], InstancePort=80)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerName')

    def test_T4460_without_policy_name(self):
        self.a1_r1.lbu.SetLoadBalancerPoliciesForBackendServer(LoadBalancerName=self.lbu_name, InstancePort=80)

    def test_T4461_without_instance_port(self):
        try:
            self.a1_r1.lbu.SetLoadBalancerPoliciesForBackendServer(LoadBalancerName=self.lbu_name, PolicyNames=[self.policy_name])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'The request must contain the parameter InstancePort')

    def test_T4462_with_invalid_policy_name(self):
        try:
            self.a1_r1.lbu.SetLoadBalancerPoliciesForBackendServer(LoadBalancerName=self.lbu_name, PolicyNames=["foo"], InstancePort=80)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'PolicyNotFound', "There is no policy with name foo for load balancer {}".format(self.lbu_name))

    def test_T4463_with_invalid_instance_port(self):
        try:
            self.a1_r1.lbu.SetLoadBalancerPoliciesForBackendServer(LoadBalancerName=self.lbu_name, PolicyNames=[self.policy_name], InstancePort=1234)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidConfigurationRequest', 'No listener configured on this port')

    @pytest.mark.tag_sec_confidentiality
    def test_T4464_with_lbu_from_other_account(self):
        try:
            self.a2_r1.lbu.SetLoadBalancerPoliciesForBackendServer(LoadBalancerName=self.lbu_name, PolicyNames=[self.policy_name], InstancePort=80)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'LoadBalancerNotFound', "There is no ACTIVE Load Balancer named '{}'".format(self.lbu_name))
