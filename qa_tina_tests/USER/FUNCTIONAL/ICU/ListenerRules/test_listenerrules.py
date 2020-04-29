import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tina.setup_tools import start_test_http_server, start_http_server
from qa_tina_tools.tools.tina.create_tools import create_load_balancer, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_lbu
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, INSTANCE_SET, PATH, KEY_PAIR, SECURITY_GROUP_ID
from qa_test_tools.config import config_constants as constants

class Test_CreateListenerRule(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.lb_name = id_generator(prefix='lbu-')
        cls.lbu_resp = None
        cls.inst_info = None
        cls.ret_reg = None
        cls.rule_name = id_generator(prefix='rn-')
        cls.inst_id_list = None
        super(Test_CreateListenerRule, cls).setup_class()
        try:
            cls.lbu_resp = create_load_balancer(cls.a1_r1, cls.lb_name, listeners=[{'InstancePort': 80,
                                                                                    'InstanceProtocol': 'HTTP',
                                                                                    'Protocol': 'HTTP',
                                                                                    'LoadBalancerPort': 80}],
                                                availability_zones=[cls.a1_r1.config.region.az_name])
            cls.inst_info = create_instances(cls.a1_r1, nb=4)
            print("kaka")
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=cls.inst_info[SECURITY_GROUP_ID],
                                                        IpProtocol='tcp',
                                                        FromPort=80, ToPort=80,
                                                        CidrIp=Configuration.get('cidr', 'allips'))
            cls.inst_id_list = [{'InstanceId': cls.inst_info[INSTANCE_ID_LIST][i]} for i in range(4)]
            kp_info = cls.inst_info[KEY_PAIR]
            for i in range(4):
                start_http_server(cls.inst_info[INSTANCE_SET][i]['ipAddress'], kp_info[PATH],
                                  cls.a1_r1.config.region.get_info(constants.CENTOS_USER), text=cls.inst_info[INSTANCE_ID_LIST][i])
            cls.ret_reg = cls.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=cls.lb_name, Instances=cls.inst_id_list[:2])
            cls.ld = {'LoadBalancerName': cls.lb_name, 'LoadBalancerPort': 80}
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
                delete_instances(cls.a1_r1, cls.inst_info)
            if cls.lbu_resp:
                delete_lbu(cls.a1_r1, lbu_name=cls.lb_name)
        finally:
            super(Test_CreateListenerRule, cls).teardown_class()

    def test_Txxx_forward(self):
        ret_1 = self.a1_r1.icu.CreateListenerRule(
            ListenerDescription=self.ld,
            ListenerRuleDescription={'Action': 'forward', 'RuleName': 'rule1-host', 'Priority': 1,
                                     'HostPattern': 'HostPattern-Inst1-Inst3.com'},
            Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][0]},
                       {'InstanceId': self.inst_info[INSTANCE_ID_LIST][2]}])

        ret_2 = self.a1_r1.icu.CreateListenerRule(
            ListenerDescription=self.ld,
            ListenerRuleDescription={'Action': 'forward', 'RuleName': 'rule2-path', 'Priority': 2,
                                     'PathPattern': 'PathPattern-Inst2-Inst4'},
            Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][1]},
                       {'InstanceId': self.inst_info[INSTANCE_ID_LIST][3]}])

        print("kaka")
