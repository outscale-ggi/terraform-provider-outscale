from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_load_balancer, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances, delete_lbu
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST


class Test_DeregisterInstancesFromListenerRule(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.lb_name = id_generator(prefix='lbu-')
        cls.lbu_resp = None
        cls.inst_info = None
        cls.ret_reg = None
        cls.ret_lr = None
        cls.rule_name = id_generator(prefix='rn-')
        super(Test_DeregisterInstancesFromListenerRule, cls).setup_class()
        try:
            cls.lbu_resp = create_load_balancer(cls.a1_r1, cls.lb_name)
            cls.inst_info = create_instances(cls.a1_r1, nb=6)
            cls.ret_reg = cls.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=cls.lb_name,
                                                                          Instances=[{'InstanceId': cls.inst_info[INSTANCE_ID_LIST][0]},
                                                                                     {'InstanceId': cls.inst_info[INSTANCE_ID_LIST][1]},
                                                                                     {'InstanceId': cls.inst_info[INSTANCE_ID_LIST][2]},
                                                                                     {'InstanceId': cls.inst_info[INSTANCE_ID_LIST][3]}])
            cls.ret_lr = cls.a1_r1.icu.CreateListenerRule(ListenerDescription={'LoadBalancerName': cls.lb_name, 'LoadBalancerPort': 80},
                                                          ListenerRuleDescription={'RuleName': cls.rule_name, 'Priority': 5, 'HostPattern': '*.com'},
                                                          Instances=[{'InstanceId': cls.inst_info[INSTANCE_ID_LIST][0]},
                                                                     {'InstanceId': cls.inst_info[INSTANCE_ID_LIST][1]},
                                                                     {'InstanceId': cls.inst_info[INSTANCE_ID_LIST][2]}])
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret_lr:
                cls.a1_r1.icu.DeleteListenerRule(RuleName=cls.ret_lr.response.ListenerRule.ListenerRuleDescription.RuleName)
            if cls.ret_reg:
                cls.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=cls.lb_name,
                                                                  Instances=[{'InstanceId': cls.inst_info[INSTANCE_ID_LIST][0]},
                                                                             {'InstanceId': cls.inst_info[INSTANCE_ID_LIST][1]}])
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
            if cls.lbu_resp:
                delete_lbu(cls.a1_r1, lbu_name=cls.lb_name)
        finally:
            super(Test_DeregisterInstancesFromListenerRule, cls).teardown_class()

    def test_T1755_missing_rule_name(self):
        try:
            self.a1_r1.icu.DeregisterInstancesFromListenerRule(Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][0]},
                                                                          {'InstanceId': self.inst_info[INSTANCE_ID_LIST][1]}])
            assert False, 'Call should not have been successful, missing RuleName parameter'
        except OscApiException as error:
            assert_error(error, 400, 'IcuClientException', 'Field RuleName is required')

    def test_T1756_missing_instances(self):
        try:
            self.a1_r1.icu.DeregisterInstancesFromListenerRule(RuleName=self.rule_name)
            assert False, 'Call should not have been successful, missing Instances parameter'
        except OscApiException as error:
            assert_error(error, 400, 'IcuClientException', 'Field Instances is required')

    def test_T1764_empty_instances(self):
        try:
            self.a1_r1.icu.DeregisterInstancesFromListenerRule(RuleName=self.rule_name, Instances=[]).response.Instances
            assert False, 'Call should not have been successful, empty Instances parameter'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: Instances')

    def test_T1757_unknown_rule_name(self):
        try:
            self.a1_r1.icu.DeregisterInstancesFromListenerRule(RuleName='xxxx',
                                                               Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][0]},
                                                                          {'InstanceId': self.inst_info[INSTANCE_ID_LIST][1]}])
            assert False, 'Call should not have been successful, invalid RuleName parameter'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidRule.NotFound', 'No rule found with this name: xxxx')

    def test_T1758_invalid_instance_id(self):
        try:
            self.a1_r1.icu.DeregisterInstancesFromListenerRule(RuleName=self.rule_name, Instances=[{'InstanceId': 'xxx-12345678'}])
            assert False, 'Call should not have been successful, invalid instance id parameter'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.Malformed', 'Invalid ID received: xxx-12345678. Expected format: i-')

    def test_T1759_unknown_instance_id(self):
        try:
            self.a1_r1.icu.DeregisterInstancesFromListenerRule(RuleName=self.rule_name, Instances=[{'InstanceId': 'i-12345678'}])
            assert False, 'Call should not have been successful, unknown instance id parameter'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidTarget', "The specified target does not exist: i-12345678")

    def test_T1760_unregistered_instance_id(self):
        try:
            self.a1_r1.icu.DeregisterInstancesFromListenerRule(RuleName=self.rule_name,
                                                               Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][3]}])
            assert False, 'Call should not have been successful, unregistered instance parameter'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidTarget', 'The specified target does not exist: {}'.format(self.inst_info[INSTANCE_ID_LIST][3]))

    def test_T1761_multiple_instance_id(self):
        try:
            ret = self.a1_r1.icu.DeregisterInstancesFromListenerRule(RuleName=self.rule_name,
                                                                     Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][0]},
                                                                                {'InstanceId': self.inst_info[INSTANCE_ID_LIST][1]}])
            assert len(ret.response.Instances) == 1
            assert self.inst_info[INSTANCE_ID_LIST][2] == ret.response.Instances[0].InstanceId
        finally:
            self.a1_r1.icu.RegisterInstancesWithListenerRule(RuleName=self.rule_name,
                                                             Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][0]},
                                                                        {'InstanceId': self.inst_info[INSTANCE_ID_LIST][1]}])

    def test_T1762_stopped_instance_state(self):
        try:
            instId = self.inst_info[INSTANCE_ID_LIST][0]
            stop_instances(self.a1_r1, [instId])
            ret = self.a1_r1.icu.DeregisterInstancesFromListenerRule(RuleName=self.rule_name, Instances=[{'InstanceId': instId}])
            assert len(ret.response.Instances) == 2
            inst_ids = [inst.InstanceId for inst in ret.response.Instances]
            assert self.inst_info[INSTANCE_ID_LIST][1] in inst_ids
            assert self.inst_info[INSTANCE_ID_LIST][2] in inst_ids
        finally:
            self.a1_r1.fcu.StartInstances(InstanceId=[instId])
            self.a1_r1.icu.RegisterInstancesWithListenerRule(RuleName=self.rule_name, Instances=[{'InstanceId': instId}])

    def test_T1763_invalid_instance_in_list(self):
        try:
            self.a1_r1.icu.DeregisterInstancesFromListenerRule(RuleName=self.rule_name,
                                                               Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][1]},
                                                                          {'InstanceId': self.inst_info[INSTANCE_ID_LIST][3]}])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidTarget', 'The specified target does not exist: {}'.format(self.inst_info[INSTANCE_ID_LIST][3]))
