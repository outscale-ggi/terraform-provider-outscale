
import os

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.compare_objects import verify_response, create_hints
from qa_test_tools import misc
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina import create_tools, info_keys, delete_tools


class Test_UpdateListenerRule(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.lb_name = misc.id_generator(prefix='lbu-')
        cls.lbu_resp = None
        cls.inst_info = None
        cls.ret_reg = None
        cls.rule_name = misc.id_generator(prefix='rn-')
        cls.inst_id_list = None
        super(Test_UpdateListenerRule, cls).setup_class()
        try:
            cls.lbu_resp = create_tools.create_load_balancer(cls.a1_r1, cls.lb_name)
            cls.inst_info = create_tools.create_instances(cls.a1_r1, nb=6)
            cls.inst_id_list = [{'InstanceId': cls.inst_info[info_keys.INSTANCE_ID_LIST][i]} for i in range(4)]
            cls.ret_reg = cls.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=cls.lb_name,
                                                                          Instances=cls.inst_id_list)
            cls.ld = {'LoadBalancerName': cls.lb_name, 'LoadBalancerPort': 80}
            cls.lrd = {'ListenerRuleName': cls.rule_name, 'Priority': 100, 'HostNamePattern': '*.com',
                       'PathPattern': "/.com"}
            ret = cls.a1_r1.oapi.CreateListenerRule(Listener=cls.ld,
                                              ListenerRule=cls.lrd,
                                              VmIds=cls.inst_info[info_keys.INSTANCE_ID_LIST]).response.ListenerRule
            hints = [cls.a1_r1.config.account.account_id,
                     cls.a2_r1.config.account.account_id,
                     cls.lb_name,
                     cls.rule_name,
                     str(ret.ListenerRuleId),
                     str(ret.ListenerId)]
            hints.extend(cls.inst_info[info_keys.INSTANCE_ID_LIST])
            cls.hints = create_hints(hints)
        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret_reg:
                cls.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=cls.lb_name,
                                                                  Instances=cls.inst_id_list)
            if cls.inst_info:
                delete_tools.delete_instances(cls.a1_r1, cls.inst_info)
            if cls.lbu_resp:
                delete_tools.delete_lbu(cls.a1_r1, lbu_name=cls.lb_name)
        finally:
            super(Test_UpdateListenerRule, cls).teardown_class()

    def test_T4805_with_invalid_param(self):
        try:
            self.a1_r1.oapi.UpdateListenerRule(ListenerRuleName=self.rule_name)
            assert False, 'call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, '7000', 'MissingParameter')

    def test_T4806_with_no_param(self):
        try:
            self.a1_r1.oapi.UpdateListenerRule()
            assert False, 'call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, '7000', 'MissingParameter')

    def test_T4807_with_valid_HostPattern(self):
        resp = self.a1_r1.oapi.UpdateListenerRule(ListenerRuleName=self.rule_name, HostPattern="*.abc.?.abc.*.com").response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_valid_host_pattern.json'), self.hints)


    def test_T4808_with_invalid_HostPattern(self):
        try:
            self.a1_r1.oapi.UpdateListenerRule(ListenerRuleName=self.rule_name, HostPattern=["*.abc.?.abc.*.com"])
            assert False, 'call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, '4110', 'InvalidParameterValue')

    def test_T4809_with_valid_PathPattern(self):
        resp = self.a1_r1.oapi.UpdateListenerRule(ListenerRuleName=self.rule_name, PathPattern="/.fr").response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_valid_path_pattern.json'), self.hints)

    def test_T4810_with_invalid_PathPattern(self):
        try:
            self.a1_r1.oapi.UpdateListenerRule(ListenerRuleName=self.rule_name, PathPattern=["/.fr"])
            assert False, 'call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, '4110', 'InvalidParameterValue')

    def test_T5555_with_valid_params(self):
        resp = self.a1_r1.oapi.UpdateListenerRule(ListenerRuleName=self.rule_name, HostPattern="*.abc.?.abc.*.fr", PathPattern="/.be").response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_valid_path_pattern_host_pattern.json'), self.hints)
