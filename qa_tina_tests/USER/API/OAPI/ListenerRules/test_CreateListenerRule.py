import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc 
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina import create_tools, delete_tools
from qa_tina_tools.tools.tina import info_keys


class Test_CreateListenerRule(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.lb_name = misc.id_generator(prefix='lbu-')
        cls.lbu_resp = None
        cls.inst_info = None
        cls.ret_reg = None
        cls.rule_name = misc.id_generator(prefix='rn-')
        cls.inst_id_list = None
        super(Test_CreateListenerRule, cls).setup_class()
        try:
            cls.lbu_resp = create_tools.create_load_balancer(cls.a1_r1, cls.lb_name)
            cls.inst_info = create_tools.create_instances(cls.a1_r1, nb=6)
            cls.inst_id_list = [{'InstanceId': cls.inst_info[info_keys.INSTANCE_ID_LIST][i]} for i in range(4)]
            cls.ret_reg = cls.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=cls.lb_name, Instances=cls.inst_id_list)
            cls.ld = {'LoadBalancerName': cls.lb_name, 'LoadBalancerPort': 80}
            cls.lrd = {'ListenerRuleName': cls.rule_name, 'Priority': 100, 'HostNamePattern': '*.com'}
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
            super(Test_CreateListenerRule, cls).teardown_class()

    @pytest.mark.region_qa
    def test_T4775_rule_limit_exceeded(self):
        ret_lr = None
        quota_value = None
        try:
            quota_value = self.a1_r1.intel.user.find_quotas(user=self.a1_r1.config.account.account_id, quota='lb_rules_limit').response.result
            self.a1_r1.intel.user.update(username=self.a1_r1.config.account.account_id, fields={'lb_rules_limit': 0})
            ret_lr = self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                       ListenerRule=self.lrd,
                                                       VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST])
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'TooManyResources (QuotaExceded)', 10012)
        finally:
            if quota_value is not None:
                self.a1_r1.intel.user.update(username=self.a1_r1.config.account.account_id, fields={'lb_rules_limit': quota_value})
            if ret_lr:
                self.a1_r1.oapi.DeleteListenerRule(RuleName=ret_lr.response.ListenerRule.ListenerRuleName)

    def check_error(self, status, code, msg, ld=None, lrd=None, inst_ids=None):
        if not ld:
            ld = self.ld
        if not lrd:
            lrd = self.lrd
        if not inst_ids:
            inst_ids = self.inst_info[info_keys.INSTANCE_ID_LIST]
        ret_lr = None
        try:
            ret_lr = self.a1_r1.oapi.CreateListenerRule(Listener=ld, ListenerRule=lrd, VmIds=inst_ids)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, status, msg, code)
        finally:
            if ret_lr:
                self.a1_r1.oapi.DeleteListenerRule(RuleName=ret_lr.response.ListenerRule.ListenerRuleName)

    def test_T4776_with_array_of_dict_VmIds(self):
        ret_lr = None
        try:
            ret_lr = self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                        ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                      'Priority': 101, 'HostNamePattern': "*.abc.?.abc.*.com"},
                                                        VmIds=self.inst_id_list)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)
        finally:
            if ret_lr:
                self.a1_r1.oapi.DeleteListenerRule(RuleName=ret_lr.response.ListenerRule.ListenerRuleName)

    def test_T4777_too_low_priority(self):
        self.check_error(400,  "4047", 'InvalidParameterValue',
                         lrd={'ListenerRuleName': self.rule_name, 'Priority': 0, 'HostNamePattern': '*.com'})

    def test_T4778_too_high_priority(self):
        self.check_error(400, "4047", 'InvalidParameterValue',
                         lrd={'ListenerRuleName': self.rule_name, 'Priority': 20000, 'HostNamePattern': '*.com'})

    def test_T4779_missing_vms(self):
        ret_lr = None
        try:
            ret_lr = self.a1_r1.oapi.CreateListenerRule(Listener=self.ld, ListenerRule=self.lrd)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'MissingParameter', 7000)
        finally:
            if ret_lr:
                self.a1_r1.oapi.DeleteListenerRule(RuleName=ret_lr.response.ListenerRule.ListenerRuleName)

    def test_T4780_incorrect_type_vms(self):
        self.check_error(400, '4110', 'InvalidParameterValue', inst_ids=[self.inst_info[info_keys.INSTANCE_ID_LIST]])

    def test_T4781_missing_list_desc(self):
        ret_lr = None
        try:
            ret_lr = self.a1_r1.oapi.CreateListenerRule(ListenerRule=self.lrd, VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'MissingParameter', 7000)
        finally:
            if ret_lr:
                self.a1_r1.oapi.DeleteListenerRule(ListenerRuleName=ret_lr.response.ListenerRule.ListenerRuleName)

    def test_T4783_incorrect_type_list_desc(self):
        self.check_error(400, '4110', "InvalidParameterValue", ld=[self.ld])

    def test_T4784_missing_ld_lbu_name(self):
        self.check_error(400, '7000', "MissingParameter", ld={'LoadBalancerPort': 80})

    def test_T4785_missing_ld_lbu_port(self):
        self.check_error(400, '7000', "MissingParameter", ld={'LoadBalancerName': self.lb_name})

    def test_T4786_incorrect_type_ld_lbu_name(self):
        self.check_error(400, '4110', "InvalidParameterValue",
                         ld={'LoadBalancerName': 1234, 'LoadBalancerPort': 80})

    def test_T4787_incorrect_type_ld_lbu_port(self):
        self.check_error(400, '4110', "InvalidParameterValue",
                         ld={'LoadBalancerName': self.lb_name, 'LoadBalancerPort': 'xxx'})

    def test_T4788_missing_list_rule_desc(self):
        ret_lr = None
        try:
            ret_lr = self.a1_r1.oapi.CreateListenerRule(Listener=self.ld, VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'MissingParameter', 7000)
        finally:
            if ret_lr:
                self.a1_r1.oapi.DeleteListenerRule(ListenerRuleName=ret_lr.response.ListenerRule.ListenerRuleName)

    def test_T4789_incorrect_type_list_rule_desc(self):
        self.check_error(400, '4110', "InvalidParameterValue",
                         lrd=[{'ListenerRuleName': self.rule_name, 'Priority': 100, 'HostNamePattern': '*.com'}])

    def test_T4790_missing_lrd_priority(self):
        self.check_error(400, '7000', "MissingParameter",
                         lrd={'ListenerRuleName': self.rule_name, 'HostNamePattern': '*.com'})

    def test_T4791_lrd_same_priority(self):
        ret_lr = None
        try:
            ret_lr = self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                        ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                      'Priority': 100,
                                                                      'HostNamePattern': '*.com'},
                                                        VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST])
            self.check_error(409, '9047', "ResourceConflict")
        finally:
            if ret_lr:
                self.a1_r1.oapi.DeleteListenerRule(ListenerRuleName=ret_lr.response.ListenerRule.ListenerRuleName)

    def test_T4792_incorrect_content_lrd_action(self):
        try:
            self.check_error(400, '7000', "MissingParameter",
                             lrd={'Action': 'xxx', 'ListenerRuleName': self.rule_name, 'Priority': 100, 'HostNamePattern': '*.com'})
            assert False, 'Remove known error code'
        except AssertionError:
            known_error('TINA-4973', 'Call should have failed')
        except Exception:
            assert False, 'Remove known error code'

    def test_T4793_incorrect_content_lrd_hostpattern(self):
        msg = "InvalidParameterValue"
        self.check_error(400, '4047', msg, lrd={'ListenerRuleName': self.rule_name, 'Priority': 100, 'HostNamePattern': '_.com'})
        self.check_error(400, '4047', msg, lrd={'ListenerRuleName': self.rule_name, 'Priority': 100, 'HostNamePattern': '$.com'})
        self.check_error(400, '4047', msg, lrd={'ListenerRuleName': self.rule_name, 'Priority': 100, 'HostNamePattern': '/.com'})
        self.check_error(400, '4047', msg, lrd={'ListenerRuleName': self.rule_name, 'Priority': 100, 'HostNamePattern': '\\.com'})
        self.check_error(400, '4047', msg, lrd={'ListenerRuleName': self.rule_name, 'Priority': 100, 'HostNamePattern': '".com'})
        self.check_error(400, '4047', msg, lrd={'ListenerRuleName': self.rule_name, 'Priority': 100, 'HostNamePattern': "'.com"})
        self.check_error(400, '4047', msg, lrd={'ListenerRuleName': self.rule_name, 'Priority': 100, 'HostNamePattern': "@.com"})
        self.check_error(400, '4047', msg, lrd={'ListenerRuleName': self.rule_name, 'Priority': 100, 'HostNamePattern': ":.com"})
        self.check_error(400, '4047', msg, lrd={'ListenerRuleName': self.rule_name, 'Priority': 100, 'HostNamePattern': "+.com"})
        self.check_error(400, '4047', msg, lrd={'ListenerRuleName': self.rule_name, 'Priority': 100, 'HostNamePattern': "*.abc.*.abc.*.abc.*.com"})
        self.check_error(400, '4047', msg, lrd={'ListenerRuleName': self.rule_name, 'Priority': 100, 'HostNamePattern': "1234567890" * 13})

    def test_T4794_valid_lrd_hostpattern(self):
        ret_lr = []
        try:
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                           'Priority': 100, 'HostNamePattern': "*.abc.*.abc.*.com"},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                           'Priority': 101, 'HostNamePattern': "*.abc.?.abc.*.com"},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                           'Priority': 102, 'HostNamePattern': "*.abc.-.abc.*.com"},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                           'Priority': 103, 'HostNamePattern': "1234567890" * 12 + '12345678'},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
        finally:
            for ret in ret_lr:
                self.a1_r1.oapi.DeleteListenerRule(ListenerRuleName=ret.response.ListenerRule.ListenerRuleName)

    def test_T4795_incorrect_content_lrd_pathpattern(self):
        msg = 'Invalid value received for \'PathPattern\': ;.com. Supported patterns: ^[\w\_\-\.\$\/\~\\\"\\\'\@\:\+\&\*\?]{,128}$'
        self.check_error(400, '4110', 'InvalidParameterValue', msg, lrd={'ListenerRuleName': self.rule_name, 'Priority': 100, 'PathPattern': ';.com'})
        self.check_error(400, '4110', 'InvalidParameterValue', 'Invalid value received for \'PathPattern\': *.abc.*.abc.*.abc.*.com. Max wildcards supported: 3',
                         lrd={'ListenerRuleName': self.rule_name, 'Priority': 100, 'PathPattern': "*.abc.*.abc.*.abc.*.com"})
        self.check_error(400, '4110', 'InvalidParameterValue', ("Invalid value received for 'PathPattern': 12345678901234567890123456789012345678901234567890123456789"
                                                        "01234567890123456789012345678901234567890123456789012345678901234567890. Supported patterns:"
                                                        " ^[\w\_\-\.\$\/\~\\\"\\\'\@\:\+\&\*\?]{,128}$"), lrd={'ListenerRuleName': self.rule_name, 'Priority': 100,
                                                                                                               'PathPattern': "1234567890" * 13})

    def test_T4796_valid_lrd_pathpattern(self):
        ret_lr = []
        try:
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                           'Priority': 100, 'PathPattern': "*.abc.*.abc.*.com"},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                                      'Priority': 101, 'PathPattern': "_.com"},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                                      'Priority': 103, 'PathPattern': "$.com"},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                                      'Priority': 104, 'PathPattern': "/.com"},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                                      'Priority': 105, 'PathPattern': "~.com"},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                                      'Priority': 107, 'PathPattern': '".com'},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                                      'Priority': 108, 'PathPattern': "@.com"},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                                      'Priority': 109, 'PathPattern': ":.com"},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                                      'Priority': 110, 'PathPattern': "+.com"},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                                      'Priority': 111, 'PathPattern': "?.com"},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                                      'Priority': 112, 'PathPattern': "?.com"},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                                      'Priority': 113, 'PathPattern': "1234567890" * 12 + '12345678'},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
            ret_lr.append(self.a1_r1.oapi.CreateListenerRule(Listener=self.ld,
                                                             ListenerRule={'ListenerRuleName': misc.id_generator(prefix='rn-'),
                                                                                      'Priority': 102, 'PathPattern': "-.com"},
                                                             VmIds=self.inst_info[info_keys.INSTANCE_ID_LIST]))
        finally:
            for ret in ret_lr:
                self.a1_r1.oapi.DeleteListenerRule(ListenerRuleName=ret.response.ListenerRule.ListenerRuleName)

    def test_T4797_incorrect_content_lrd_ruleid(self):
        self.check_error(400, '3001', "InvalidParameter",
                         lrd={'RuleId': 'xxx', 'ListenerRuleName': self.rule_name, 'Priority': 100, 'HostNamePattern': '*.com'})
        known_error('TINA-4973', 'This call should not be accepted, as RuleId should only be used in the response')

    def test_T4798_incorrect_content_lrd_rulename(self):
        self.check_error(400, '4110', "InvalidParameterValue", lrd={'ListenerRuleName': 12345, 'Priority': 100, 'HostNamePattern': '*.com'})
