from qa_test_tools import misc
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina import create_tools, info_keys, delete_tools


class Test_ReadListenerRules(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.lb_name = misc.id_generator(prefix='lbu-')
        cls.lbu_resp = None
        cls.inst_info = None
        cls.ret_reg = None
        cls.rule_name = misc.id_generator(prefix='rn-')
        cls.inst_id_list = None
        cls.rname = None
        super(Test_ReadListenerRules, cls).setup_class()
        try:
            cls.lbu_resp = create_tools.create_load_balancer(cls.a1_r1, cls.lb_name)
            cls.inst_info = create_tools.create_instances(cls.a1_r1, nb=6)
            cls.inst_id_list = [{'InstanceId': cls.inst_info[info_keys.INSTANCE_ID_LIST][i]} for i in range(4)]
            cls.ret_reg = cls.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=cls.lb_name,
                                                                          Instances=cls.inst_id_list)
            cls.ld = {'LoadBalancerName': cls.lb_name, 'LoadBalancerPort': 80}
            cls.lrd = {'ListenerRuleName': cls.rule_name, 'Priority': 100, 'HostNamePattern': '*.com',
                       'PathPattern': "/.com"}
            cls.rname = cls.a1_r1.oapi.CreateListenerRule(Listener=cls.ld,
                                                          ListenerRule=cls.lrd,
                                                          VmIds=cls.inst_info[
                                                              info_keys.INSTANCE_ID_LIST]).response.ListenerRule.ListenerRuleName
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
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
            super(Test_ReadListenerRules, cls).teardown_class()

    def test_T4802_with_not_existing_param_value(self):
        ret = self.a1_r1.oapi.ReadListenerRules(Filters={'ListenerRuleNames': ['toto']})
        assert len(ret.response.ListenerRules) == 0

    def test_T4803_with_no_param(self):
        ret = self.a1_r1.oapi.ReadListenerRules()
        assert len(ret.response.ListenerRules) > 0

    def test_T4804_with_valid_param(self):
        ret = self.a1_r1.oapi.ReadListenerRules(Filters={'ListenerRuleNames': [self.rname]})
        ret.check_response()
