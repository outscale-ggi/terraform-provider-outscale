

from qa_test_tools.test_base import OscTestSuite


class Test_ReadQuotas(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadQuotas, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ReadQuotas, cls).teardown_class()

    def test_T3679_empty_filters(self):
        ret = self.a1_r1.oapi.ReadQuotas().response.QuotaTypes
        assert len(ret) >= 1
        quota_global = next((x for x in ret if x.QuotaType == 'global'), None)
        assert quota_global
        assert len(quota_global.Quotas) == 44
        for quota in quota_global.Quotas:
            assert quota.AccountId == self.a1_r1.config.account.account_id
            assert quota.Name
            assert quota.ShortDescription
            assert quota.QuotaCollection
            assert hasattr(quota, 'MaxValue')
            assert hasattr(quota, 'UsedValue')

    def test_T3680_filters_quota_names(self):
        ret = self.a1_r1.oapi.ReadQuotas(Filters={'QuotaNames': ['vm_limit']}).response.QuotaTypes
        assert len(ret) >= 1
        assert ret[0].QuotaType == 'global'
        assert len(ret[0].Quotas) == 1
        assert ret[0].Quotas[0].AccountId == self.a1_r1.config.account.account_id
        assert ret[0].Quotas[0].Name == 'vm_limit'

    def test_T3681_filters_invalid_quota_names(self):
        ret = self.a1_r1.oapi.ReadQuotas(Filters={'QuotaNames': ['foo']}).response.QuotaTypes
        assert len(ret) == 0

    def test_T3682_filters_quota_short_descriptions(self):
        ret = self.a1_r1.oapi.ReadQuotas(Filters={'ShortDescriptions': ['VM Limit']}).response.QuotaTypes
        assert len(ret) >= 1
        assert ret[0].QuotaType == 'global'
        assert len(ret[0].Quotas) == 1
        assert ret[0].Quotas[0].AccountId == self.a1_r1.config.account.account_id
        assert ret[0].Quotas[0].ShortDescription == 'VM Limit'

    def test_T3683_filters_quota_collections(self):
        ret = self.a1_r1.oapi.ReadQuotas(Filters={'Collections': ['Compute']}).response.QuotaTypes
        assert len(ret) == 1
        assert ret[0].QuotaType == 'global'
        assert len(ret[0].Quotas) == 6
        for quota in ret[0].Quotas:
            assert quota.QuotaCollection == 'Compute'

    def test_T3684_filters_quota_types(self):
        ret = self.a1_r1.oapi.ReadQuotas(Filters={'QuotaTypes': ['global']}).response.QuotaTypes
        assert len(ret) == 1
        assert ret[0].QuotaType == 'global'
        assert len(ret[0].Quotas) == 46

    def test_T3685_filters_invalid_quota_short_descriptions(self):
        ret = self.a1_r1.oapi.ReadQuotas(Filters={'ShortDescriptions': ['foo']}).response.QuotaTypes
        assert len(ret) == 0

    def test_T3686_filters_invalid_quota_collections(self):
        ret = self.a1_r1.oapi.ReadQuotas(Filters={'Collections': ['foo']}).response.QuotaTypes
        assert len(ret) == 0

    def test_T3687_filters_invalid_quota_types(self):
        ret = self.a1_r1.oapi.ReadQuotas(Filters={'QuotaTypes': ['foo']}).response.QuotaTypes
        assert len(ret) == 0
