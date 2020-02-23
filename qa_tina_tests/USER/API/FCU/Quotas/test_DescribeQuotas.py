# pylint: disable=missing-docstring

from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import assert_error
from qa_common_tools.test_base import OscTestSuite, known_error


class Test_DescribeQuotas(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeQuotas, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeQuotas, cls).teardown_class()

    def test_T3470_no_params(self):
        ret = self.a1_r1.fcu.DescribeQuotas()
        assert len(ret.response.referenceQuotaSet) >= 1
        assert ret.response.referenceQuotaSet[0].reference == 'global'
        assert len(ret.response.referenceQuotaSet[0].quotaSet) == 43
        for quota in ret.response.referenceQuotaSet[0].quotaSet:
            assert quota.ownerId == self.a1_r1.config.account.account_id
            assert quota.name
            assert quota.displayName
            assert quota.groupName
            assert quota.maxQuotaValue
            assert quota.usedQuotaValue

    def test_T3471_with_quota_name(self):
        ret = self.a1_r1.fcu.DescribeQuotas(QuotaName=['vm_limit'])
        assert len(ret.response.referenceQuotaSet) >= 1
        assert ret.response.referenceQuotaSet[0].reference == 'global'
        assert len(ret.response.referenceQuotaSet[0].quotaSet) == 1
        assert ret.response.referenceQuotaSet[0].quotaSet[0].ownerId == self.a1_r1.config.account.account_id
        assert ret.response.referenceQuotaSet[0].quotaSet[0].name == 'vm_limit'

    def test_T3472_with_invalid_quota_name(self):
        try:
            self.a1_r1.fcu.DescribeQuotas(QuotaName=['foo'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', "These quotas are not yet implemented: ['foo'].")

    def test_T3473_with_filter_display_name(self):
        ret = self.a1_r1.fcu.DescribeQuotas(Filter=[{'Name': 'quota.display-name', 'Value': ['VM Limit']}])
        assert len(ret.response.referenceQuotaSet) >= 1
        assert ret.response.referenceQuotaSet[0].reference == 'global'
        assert len(ret.response.referenceQuotaSet[0].quotaSet) == 1
        assert ret.response.referenceQuotaSet[0].quotaSet[0].ownerId == self.a1_r1.config.account.account_id
        assert ret.response.referenceQuotaSet[0].quotaSet[0].displayName == 'VM Limit'

    def test_T3474_with_filter_group_name(self):
        ret = self.a1_r1.fcu.DescribeQuotas(Filter=[{'Name': 'quota.group-name', 'Value': ['Compute']}])
        assert len(ret.response.referenceQuotaSet) == 1
        assert ret.response.referenceQuotaSet[0].reference == 'global'
        assert len(ret.response.referenceQuotaSet[0].quotaSet) == 6
        for quota in ret.response.referenceQuotaSet[0].quotaSet:
            assert quota.groupName == 'Compute'

    def test_T3475_with_filter_reference(self):
        ret = self.a1_r1.fcu.DescribeQuotas(Filter=[{'Name': 'reference', 'Value': ['global']}])
        assert len(ret.response.referenceQuotaSet) >= 1
        assert ret.response.referenceQuotaSet[0].reference == 'global'
        assert len(ret.response.referenceQuotaSet[0].quotaSet) == 45

    def test_T3476_with_filter_invalid_display_name(self):
        ret = self.a1_r1.fcu.DescribeQuotas(Filter=[{'Name': 'quota.display-name', 'Value': ['foo']}])
        assert not ret.response.referenceQuotaSet

    def test_T3477_with_filter_invalid_group_name(self):
        ret = self.a1_r1.fcu.DescribeQuotas(Filter=[{'Name': 'quota.group-name', 'Value': ['foo']}])
        assert not ret.response.referenceQuotaSet

    def test_T3478_with_filter_invalid_reference(self):
        ret = self.a1_r1.fcu.DescribeQuotas(Filter=[{'Name': 'reference', 'Value': ['foo']}])
        assert not ret.response.referenceQuotaSet

    def test_T3479_with_invalid_filter(self):
        try:
            self.a1_r1.fcu.DescribeQuotas(Filter=[{'Name': 'foo', 'Value': ['bar']}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "The filter 'foo' is invalid")
