from osc_common.exceptions import OscApiException
from qa_common_tools.misc import assert_error
from qa_common_tools.test_base import OscTestSuite

class Test_find_for_account(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_find_for_account, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_find_for_account, cls).teardown_class()

    def test_T4416_with_owner_id(self):
        ret = self.a1_r1.intel.quota.find_for_account(owner=self.a1_r1.config.account.account_id)
        assert ret.response.result.definitions and len(ret.response.result.definitions) >= 1
        for i in ret.response.result.definitions:
            assert i.name
            assert i.quotas
        assert ret.response.result.used
        for i in getattr(ret.response.result.used, 'osc_global'):
            assert i.display_name
            assert i.description
            assert i.name
            assert type(i.used_quota_value) == int
            assert i.group_name
            assert type(i.max_quota_value) == int
            assert i.owner_id
        assert getattr(ret.response.result.limits, 'accesskey_limit')
        assert getattr(ret.response.result.limits, 'bypass_group_limit')
        assert getattr(ret.response.result.limits, 'bypass_vpc_limit')
        assert getattr(ret.response.result.limits, 'bgp_route_limit')
        assert getattr(ret.response.result.limits, 'bypass_group_size_limit')
        assert getattr(ret.response.result.limits, 'certificate_limit')


    def test_T4417_without_params(self):
        try:
            self.a1_r1.intel.quota.find_for_account()
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 200, 0, "missing-parameter - Parameter cannot be empty: Owner")

    def test_T4418_with_filter_display_name(self):
        ret = self.a1_r1.intel.quota.find_for_account(owner=self.a1_r1.config.account.account_id,
                                                      display_names=['Security Groups Rules Limit'])
        sg = self.a1_r1.oapi.ReadSecurityGroups()
        for i in sg.response.SecurityGroups:
            for j in getattr(ret.response.result.used, i.SecurityGroupId.replace('-', '_')):
                assert j.display_name == 'Security Groups Rules Limit'

    def test_T4419_with_filter_quota_name(self):
        ret = self.a1_r1.intel.quota.find_for_account(owner=self.a1_r1.config.account.account_id,
                                                      quota_names=['sg_rule_limit'])
        sg = self.a1_r1.oapi.ReadSecurityGroups()
        for i in sg.response.SecurityGroups:
            for j in getattr(ret.response.result.used, i.SecurityGroupId.replace('-', '_')):
                assert j.name == 'sg_rule_limit'

    def test_T4420_with_filter_group_name(self):
        ret = self.a1_r1.intel.quota.find_for_account(owner=self.a1_r1.config.account.account_id,
                                                      group_names=['Security Groups'])
        sg = self.a1_r1.oapi.ReadSecurityGroups()
        for i in sg.response.SecurityGroups:
            for j in getattr(ret.response.result.used, i.SecurityGroupId.replace('-', '_')):
                assert j.group_name == 'Security Groups'

    def test_T4421_with_mix_filter_group_name_filter_name(self):
        filter_dict = {'display_names': ['VPC Security Groups Rules Limit'], 'group_names': ['Security Groups']}
        ret = self.a1_r1.intel.quota.find_for_account(owner=self.a1_r1.config.account.account_id, **filter_dict)
        for i in getattr(ret.response.result.used, 'osc_global'):
            assert i.group_name == 'Security Groups'
            assert i.display_name == 'VPC Security Groups Rules Limit'
