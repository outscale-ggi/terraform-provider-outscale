import pytest
import requests

from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.setup_tools import start_http_server
from qa_tina_tools.tools.tina.create_tools import create_load_balancer, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_lbu
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, INSTANCE_SET, PATH, KEY_PAIR, SECURITY_GROUP_ID


class Test_listenerrules(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.lb_name = id_generator(prefix='lbu-')
        cls.lbu_resp = None
        cls.inst_info = None
        cls.ret_reg = None
        cls.rule_name = id_generator(prefix='rn-')
        cls.inst_id_list = []
        super(Test_listenerrules, cls).setup_class()
        try:
            cls.lbu_resp = create_load_balancer(cls.a1_r1, cls.lb_name, listeners=[{'InstancePort': 80,
                                                                                    'InstanceProtocol': 'HTTP',
                                                                                    'Protocol': 'HTTP',
                                                                                    'LoadBalancerPort': 80}],
                                                availability_zones=[cls.a1_r1.config.region.az_name])
            cls.inst_info = create_instances(cls.a1_r1, nb=4)
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=cls.inst_info[SECURITY_GROUP_ID],
                                                        IpProtocol='tcp',
                                                        FromPort=80, ToPort=80,
                                                        CidrIp=Configuration.get('cidr', 'allips'))
            cls.inst_id_list = [{'InstanceId': cls.inst_info[INSTANCE_ID_LIST][i]} for i in range(4)]
            kp_info = cls.inst_info[KEY_PAIR]
            for i in [0, 2]:
                start_http_server(cls.inst_info[INSTANCE_SET][i]['ipAddress'], kp_info[PATH],
                                  cls.a1_r1.config.region.get_info(constants.CENTOS_USER), text=cls.inst_info[INSTANCE_ID_LIST][i])
            for i in [1, 3]:
                start_http_server(cls.inst_info[INSTANCE_SET][i]['ipAddress'], kp_info[PATH],
                                  cls.a1_r1.config.region.get_info(constants.CENTOS_USER),
                                  text=cls.inst_info[INSTANCE_ID_LIST][i], is_path=True, path_dir='PathPattern-Inst2-Inst4')
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
                cls.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=cls.lb_name, Instances=cls.inst_id_list[:2])
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
            if cls.lbu_resp:
                delete_lbu(cls.a1_r1, lbu_name=cls.lb_name)
        finally:
            super(Test_listenerrules, cls).teardown_class()

    def test_T4926_forward(self):
        if self.a1_r1.config.account.login.startswith('qa'):
            pytest.skip("need configuration")
        try:
            ret_lr_1 = self.a1_r1.icu.CreateListenerRule(
                ListenerDescription=self.ld,
                ListenerRuleDescription={'Action': 'forward', 'RuleName': 'rule89-host', 'Priority': 1,
                                         'HostPattern': 'HostPattern-Inst1-Inst3.com'},
                Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][0]},
                           {'InstanceId': self.inst_info[INSTANCE_ID_LIST][2]}])


            ret_lr_2 = self.a1_r1.icu.CreateListenerRule(
                ListenerDescription=self.ld,
                ListenerRuleDescription={'Action': 'forward', 'RuleName': 'rule99-path', 'Priority': 2,
                                         'PathPattern': 'PathPattern-Inst2-Inst4'},
                Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][1]},
                           {'InstanceId': self.inst_info[INSTANCE_ID_LIST][3]}])

            response = requests.get("http://HostPattern-Inst1-Inst3.com")
            assert response.text in [self.inst_info[INSTANCE_ID_LIST][0]+'\n', self.inst_info[INSTANCE_ID_LIST][2]+'\n']
            #TODO request of pathpattern
        finally:
            if ret_lr_1:
                self.a1_r1.icu.DeleteListenerRule(RuleName=ret_lr_1.response.ListenerRule.ListenerRuleDescription.RuleName)
            if ret_lr_2:
                self.a1_r1.icu.DeleteListenerRule(RuleName=ret_lr_2.response.ListenerRule.ListenerRuleDescription.RuleName)