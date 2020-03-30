import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_load_balancer, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_lbu
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST


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
            cls.lbu_resp = create_load_balancer(cls.a1_r1, cls.lb_name)
            cls.inst_info = create_instances(cls.a1_r1, nb=6)
            cls.inst_id_list = [{'InstanceId': cls.inst_info[INSTANCE_ID_LIST][i]} for i in range(4)]
            cls.ret_reg = cls.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=cls.lb_name, Instances=cls.inst_id_list)
            cls.ld = {'LoadBalancerName': cls.lb_name, 'LoadBalancerPort': 80}
            cls.lrd = {'RuleName': cls.rule_name, 'Priority': 100, 'HostPattern': '*.com'}
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

    @pytest.mark.region_qa
    def test_T1619_rule_limit_exceeded(self):
        ret_lr = None
        quota_value = None
        try:
            quota_value = self.a1_r1.intel.user.find_quotas(user=self.a1_r1.config.account.account_id, quota='lb_rules_limit').response.result
            self.a1_r1.intel.user.update(username=self.a1_r1.config.account.account_id, fields={'lb_rules_limit': 0})
            ret_lr = self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                       ListenerRuleDescription=self.lrd,
                                                       Instances=self.inst_id_list)
        except OscApiException as error:
            assert_error(error, 400, 'ListenerRulesLimitExceeded', "The limit has exceeded: 0.")
        finally:
            if quota_value is not None:
                self.a1_r1.intel.user.update(username=self.a1_r1.config.account.account_id, fields={'lb_rules_limit': quota_value})
            if ret_lr:
                self.a1_r1.icu.DeleteListenerRule(RuleName=ret_lr.response.ListenerRule.ListenerRuleDescription.RuleName)

    def check_error(self, status, code, msg, ld=None, lrd=None, inst_ids=None):
        if not ld:
            ld = self.ld
        if not lrd:
            lrd = self.lrd
        if not inst_ids:
            inst_ids = self.inst_id_list
        ret_lr = None
        try:
            ret_lr = self.a1_r1.icu.CreateListenerRule(ListenerDescription=ld, ListenerRuleDescription=lrd, Instances=inst_ids)
            self.a1_r1.icu.DeleteListenerRule(RuleName=ret_lr.response.ListenerRule.ListenerRuleDescription.RuleName)
            ret_lr = None
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, status, code, msg)
        finally:
            if ret_lr:
                self.a1_r1.icu.DeleteListenerRule(RuleName=ret_lr.response.ListenerRule.ListenerRuleDescription.RuleName)

    def test_T1765_too_low_priority(self):
        self.check_error(400, 'InvalidParameterValue',
                         "Value of parameter 'Priority' is not valid: 0. Supported values: (1, 19999), please interpret 'None' as no-limit.",
                         lrd={'RuleName': self.rule_name, 'Priority': 0, 'HostPattern': '*.com'})

    def test_T1766_too_high_priority(self):
        self.check_error(400, 'InvalidParameterValue',
                         "Value of parameter 'Priority' is not valid: 20000. Supported values: (1, 19999), please interpret 'None' as no-limit.",
                         lrd={'RuleName': self.rule_name, 'Priority': 20000, 'HostPattern': '*.com'})

    def test_T1831_missing_instances(self):
        ret_lr = None
        try:
            ret_lr = self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld, ListenerRuleDescription=self.lrd)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'IcuClientException', "Field Instances is required")
        finally:
            if ret_lr:
                self.a1_r1.icu.DeleteListenerRule(RuleName=ret_lr.response.ListenerRule.ListenerRuleDescription.RuleName)

    def test_T1832_incorrect_type_instances(self):
        self.check_error(400, 'IcuClientException', "Invalid type, Instances[] must be a structure", inst_ids=[self.inst_id_list])

    def test_T1833_missing_list_desc(self):
        ret_lr = None
        try:
            ret_lr = self.a1_r1.icu.CreateListenerRule(ListenerRuleDescription=self.lrd, Instances=self.inst_id_list)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'IcuClientException', "Field ListenerDescription is required")
        finally:
            if ret_lr:
                self.a1_r1.icu.DeleteListenerRule(RuleName=ret_lr.response.ListenerRule.ListenerRuleDescription.RuleName)

    def test_T1834_incorrect_type_list_desc(self):
        self.check_error(400, 'IcuClientException', "Invalid type, ListenerDescription must be a structure", ld=[self.ld])

    def test_T1835_missing_ld_lbu_name(self):
        self.check_error(400, 'IcuClientException', "Field ListenerDescription.LoadBalancerName is required", ld={'LoadBalancerPort': 80})

    def test_T1836_missing_ld_lbu_port(self):
        self.check_error(400, 'IcuClientException', "Field ListenerDescription.LoadBalancerPort is required", ld={'LoadBalancerName': self.lb_name})

    def test_T1837_incorrect_type_ld_lbu_name(self):
        self.check_error(400, 'IcuClientException', "Invalid type, ListenerDescription.LoadBalancerName must be a string",
                         ld={'LoadBalancerName': 1234, 'LoadBalancerPort': 80})

    def test_T1838_incorrect_type_ld_lbu_port(self):
        self.check_error(400, 'IcuClientException', "Invalid type, ListenerDescription.LoadBalancerPort must be an integer",
                         ld={'LoadBalancerName': self.lb_name, 'LoadBalancerPort': 'xxx'})

    def test_T1839_missing_list_rule_desc(self):
        ret_lr = None
        try:
            ret_lr = self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld, Instances=self.inst_id_list)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'IcuClientException', "Field ListenerRuleDescription is required")
        finally:
            if ret_lr:
                self.a1_r1.icu.DeleteListenerRule(RuleName=ret_lr.response.ListenerRule.ListenerRuleDescription.RuleName)

    def test_T1840_incorrect_type_list_rule_desc(self):
        self.check_error(400, 'IcuClientException', "Invalid type, ListenerRuleDescription must be a structure",
                         lrd=[{'RuleName': self.rule_name, 'Priority': 100, 'HostPattern': '*.com'}])

    def test_T1841_missing_lrd_priority(self):
        self.check_error(400, 'IcuClientException', "Field ListenerRuleDescription.Priority is required",
                         lrd={'RuleName': self.rule_name, 'HostPattern': '*.com'})

    def test_T1849_lrd_same_priority(self):
        ret_lr = None
        try:
            ret_lr = self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                       ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                'Priority': 100,
                                                                                'HostPattern': '*.com'},
                                                       Instances=self.inst_id_list)
            self.check_error(400, 'InvalidPriority.InUse', "This priority '100' is already in use with another Rule")
        except Exception as error:
            raise error
        finally:
            if ret_lr:
                self.a1_r1.icu.DeleteListenerRule(RuleName=ret_lr.response.ListenerRule.ListenerRuleDescription.RuleName)

    def test_T1842_incorrect_content_lrd_action(self):
        try:
            self.check_error(400, 'IcuClientException', "Field Instances is required",
                             lrd={'Action': 'xxx', 'RuleName': self.rule_name, 'Priority': 100, 'HostPattern': '*.com'})
        except AssertionError:
            known_error('TINA-4973', 'Call should have failed')
        except Exception:
            assert False, 'Remove known error code'

    def test_T1843_incorrect_content_lrd_hostpattern(self):
        msg = "Invalid value received for 'HostPattern': _.com. Supported patterns: ^[a-zA-Z0-9.*?-]{,128}$"
        self.check_error(400, 'InvalidParameterValue', msg, lrd={'RuleName': self.rule_name, 'Priority': 100, 'HostPattern': '_.com'})
        self.check_error(400, 'InvalidParameterValue', "Invalid value received for 'HostPattern': $.com. Supported patterns: ^[a-zA-Z0-9.*?-]{,128}$",
                         lrd={'RuleName': self.rule_name, 'Priority': 100, 'HostPattern': '$.com'})
        self.check_error(400, 'InvalidParameterValue', "Invalid value received for 'HostPattern': /.com. Supported patterns: ^[a-zA-Z0-9.*?-]{,128}$",
                         lrd={'RuleName': self.rule_name, 'Priority': 100, 'HostPattern': '/.com'})
        self.check_error(400, 'InvalidParameterValue', "Invalid value received for 'HostPattern': \\.com. Supported patterns: ^[a-zA-Z0-9.*?-]{,128}$",
                         lrd={'RuleName': self.rule_name, 'Priority': 100, 'HostPattern': '\\.com'})
        self.check_error(400, 'InvalidParameterValue', "Invalid value received for 'HostPattern': \".com. Supported patterns: ^[a-zA-Z0-9.*?-]{,128}$",
                         lrd={'RuleName': self.rule_name, 'Priority': 100, 'HostPattern': '".com'})
        self.check_error(400, 'InvalidParameterValue', "Invalid value received for 'HostPattern': '.com. Supported patterns: ^[a-zA-Z0-9.*?-]{,128}$",
                         lrd={'RuleName': self.rule_name, 'Priority': 100, 'HostPattern': "'.com"})
        self.check_error(400, 'InvalidParameterValue', "Invalid value received for 'HostPattern': @.com. Supported patterns: ^[a-zA-Z0-9.*?-]{,128}$",
                         lrd={'RuleName': self.rule_name, 'Priority': 100, 'HostPattern': "@.com"})
        self.check_error(400, 'InvalidParameterValue', "Invalid value received for 'HostPattern': :.com. Supported patterns: ^[a-zA-Z0-9.*?-]{,128}$",
                         lrd={'RuleName': self.rule_name, 'Priority': 100, 'HostPattern': ":.com"})
        self.check_error(400, 'InvalidParameterValue', "Invalid value received for 'HostPattern': +.com. Supported patterns: ^[a-zA-Z0-9.*?-]{,128}$",
                         lrd={'RuleName': self.rule_name, 'Priority': 100, 'HostPattern': "+.com"})
        self.check_error(400, 'InvalidParameterValue', "Invalid value received for 'HostPattern': *.abc.*.abc.*.abc.*.com. Max wildcards supported: 3",
                         lrd={'RuleName': self.rule_name, 'Priority': 100, 'HostPattern': "*.abc.*.abc.*.abc.*.com"})
        self.check_error(400, 'InvalidParameterValue', ("Invalid value received for 'HostPattern': "
                                                        "12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012"
                                                        "34567890123456789012345678901234567890. Supported patterns: ^[a-zA-Z0-9.*?-]{,128}$"),
                         lrd={'RuleName': self.rule_name, 'Priority': 100, 'HostPattern': "1234567890" * 13})

    def test_T1844_valid_lrd_hostpattern(self):
        ret_lr = []
        try:
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 100, 'HostPattern': "*.abc.*.abc.*.com"},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 101, 'HostPattern': "*.abc.?.abc.*.com"},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 102, 'HostPattern': "*.abc.-.abc.*.com"},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 103, 'HostPattern': "1234567890" * 12 + '12345678'},
                                                            Instances=self.inst_id_list))
        except OscApiException as error:
            raise error
        finally:
            for ret in ret_lr:
                self.a1_r1.icu.DeleteListenerRule(RuleName=ret.response.ListenerRule.ListenerRuleDescription.RuleName)

    def test_T1845_incorrect_content_lrd_pathpattern(self):
        msg = 'Invalid value received for \'PathPattern\': ;.com. Supported patterns: ^[\w\_\-\.\$\/\~\\\"\\\'\@\:\+\&\*\?]{,128}$'
        self.check_error(400, 'InvalidParameterValue', msg, lrd={'RuleName': self.rule_name, 'Priority': 100, 'PathPattern': ';.com'})
        self.check_error(400, 'InvalidParameterValue', 'Invalid value received for \'PathPattern\': *.abc.*.abc.*.abc.*.com. Max wildcards supported: 3',
                         lrd={'RuleName': self.rule_name, 'Priority': 100, 'PathPattern': "*.abc.*.abc.*.abc.*.com"})
        self.check_error(400, 'InvalidParameterValue', ("Invalid value received for 'PathPattern': 12345678901234567890123456789012345678901234567890123456789"
                                                        "01234567890123456789012345678901234567890123456789012345678901234567890. Supported patterns:"
                                                        " ^[\w\_\-\.\$\/\~\\\"\\\'\@\:\+\&\*\?]{,128}$"), lrd={'RuleName': self.rule_name, 'Priority': 100,
                                                                                                               'PathPattern': "1234567890" * 13})

    def test_T1846_valid_lrd_pathpattern(self):
        ret_lr = []
        try:
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 100, 'PathPattern': "*.abc.*.abc.*.com"},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 101, 'PathPattern': "_.com"},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 103, 'PathPattern': "$.com"},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 104, 'PathPattern': "/.com"},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 105, 'PathPattern': "~.com"},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 107, 'PathPattern': '".com'},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 108, 'PathPattern': "@.com"},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 109, 'PathPattern': ":.com"},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 110, 'PathPattern': "+.com"},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 111, 'PathPattern': "?.com"},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 112, 'PathPattern': "?.com"},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 113, 'PathPattern': "1234567890" * 12 + '12345678'},
                                                            Instances=self.inst_id_list))
            ret_lr.append(self.a1_r1.icu.CreateListenerRule(ListenerDescription=self.ld,
                                                            ListenerRuleDescription={'RuleName': id_generator(prefix='rn-'),
                                                                                     'Priority': 102, 'PathPattern': "-.com"},
                                                            Instances=self.inst_id_list))
        except OscApiException as error:
            raise error
        finally:
            for ret in ret_lr:
                self.a1_r1.icu.DeleteListenerRule(RuleName=ret.response.ListenerRule.ListenerRuleDescription.RuleName)

    def test_T1847_incorrect_content_lrd_ruleid(self):
        self.check_error(400, 'IcuClientException', "Invalid type, ListenerRuleDescription.RuleId must be an integer",
                         lrd={'RuleId': 'xxx', 'RuleName': self.rule_name, 'Priority': 100, 'HostPattern': '*.com'})
        known_error('TINA-4973', 'This call should not be accepted, as RuleId should only be used in the response')

    def test_T1848_incorrect_content_lrd_rulename(self):
        self.check_error(400, 'IcuClientException', "Invalid type, ListenerRuleDescription.RuleName must be a string",
                         lrd={'RuleName': 12345, 'Priority': 100, 'HostPattern': '*.com'})
