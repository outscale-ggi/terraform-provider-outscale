from qa_test_tools.test_base import OscTestSuite
from qa_test_tools import misc
from qa_tina_tools.tools.tina import create_tools, info_keys, delete_tools
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.specs.check_tools import check_oapi_response


class Test_DeleteListenerRule(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.lb_name = misc.id_generator(prefix='lbu-')
        cls.lbu_resp = None
        cls.inst_info = None
        cls.ret_reg = None
        cls.rule_name = misc.id_generator(prefix='rn-')
        cls.inst_id_list = None
        cls.rname = None
        super(Test_DeleteListenerRule, cls).setup_class()
        try:
            cls.lbu_resp = create_tools.create_load_balancer(cls.a1_r1, cls.lb_name)
            cls.inst_info = create_tools.create_instances(cls.a1_r1, nb=6)
            cls.inst_id_list = [{'InstanceId': cls.inst_info[info_keys.INSTANCE_ID_LIST][i]} for i in range(4)]
            cls.ret_reg = cls.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=cls.lb_name,
                                                                          Instances=cls.inst_id_list)
            cls.ld = {'LoadBalancerName': cls.lb_name, 'LoadBalancerPort': 80}
            cls.lrd = {'ListenerRuleName': cls.rule_name, 'Priority': 100, 'HostNamePattern': '*.com', 'PathPattern': "/.com"}
            cls.rname = cls.a1_r1.oapi.CreateListenerRule(Listener=cls.ld,
                                                          ListenerRule=cls.lrd,
                                                          VmIds=cls.inst_info[info_keys.INSTANCE_ID_LIST]).response.ListenerRule.ListenerRuleName
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
                cls.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=cls.lb_name, Instances=cls.inst_id_list)
            if cls.inst_info:
                delete_tools.delete_instances(cls.a1_r1, cls.inst_info)
            if cls.lbu_resp:
                delete_tools.delete_lbu(cls.a1_r1, lbu_name=cls.lb_name)
        finally:
            super(Test_DeleteListenerRule, cls).teardown_class()

    def test_T4799_with_invalid_param(self):
        try:
            self.a1_r1.oapi.DeleteListenerRule(ListenerRuleName='toto')
            assert False, 'call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, '5029', 'InvalidResource')

    def test_T4800_with_no_param(self):
        try:
            self.a1_r1.oapi.DeleteListenerRule()
            assert False, 'call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, '7000', 'MissingParameter')

    def test_T4801_with_valid_param(self):
        resp = self.a1_r1.oapi.DeleteListenerRule(ListenerRuleName=self.rname).response
        check_oapi_response(resp, 'DeleteListenerRuleResponse')
