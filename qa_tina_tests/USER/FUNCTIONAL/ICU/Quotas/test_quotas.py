from osc_common.exceptions import OscApiException
from qa_common_tools.misc import id_generator
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state
from qa_common_tools.test_base import assert_code


class Test_quotas(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_quotas, cls).setup_class()
        try:
            pass
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_quotas, cls).teardown_class()

    def test_T1621_init_sg_rule_count_(self):
        sg_id = None
        sg_name = id_generator(prefix="group")
        try:
            ret = self.a1_r1.icu.ReadQuotas(QuotaNames=['sg_rule_limit'])
            refs_before = [ref_quota.Reference for ref_quota in ret.response.ReferenceQuota]
            sg_id = self.a1_r1.fcu.CreateSecurityGroup(GroupName=sg_name, GroupDescription=sg_name).response.groupId
            ret = self.a1_r1.icu.ReadQuotas(QuotaNames=['sg_rule_limit'])
            refs_after = [ref_quota.Reference for ref_quota in ret.response.ReferenceQuota]
            assert sg_id not in refs_before
            assert sg_id in refs_after
            assert len(refs_before) + 1 == len(refs_after)
        finally:
            if sg_id:
                self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)

    def test_T1612_sg_rule_count_(self):
        # HACK this test only works for new accounts or account with some rules in at least one security group
        sg_id = None
        sg_name = id_generator(prefix="group")
        try:
            max_quota = -1
            sg_id = self.a1_r1.fcu.CreateSecurityGroup(GroupName=sg_name, GroupDescription=sg_name).response.groupId
            ret = self.a1_r1.icu.ReadQuotas(QuotaNames=['sg_rule_limit'])
            for ref_quota in ret.response.ReferenceQuota:
                if ref_quota.Reference == sg_id:
                    for quota in ref_quota.Quotas:
                        if quota.Name == 'sg_rule_limit':
                            max_quota = int(quota.MaxQuotaValue)
                            break
                    break
            assert max_quota > 20, 'Error quotas need to be better defined'
            for i in range(10):
                self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=sg_id, IpProtocol='tcp', FromPort=100 + i, ToPort=100 + i, CidrIp='192.2.3.4')
            for i in range(10):
                self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=sg_id, IpProtocol='tcp', FromPort=99, ToPort=99, CidrIp='192.3.2.' + str(i))
            ret = self.a1_r1.icu.ReadQuotas(QuotaNames=['sg_rule_limit'])
            for ref_quota in ret.response.ReferenceQuota:
                if ref_quota.Reference == sg_id:
                    new_max_quota = int(ref_quota.Quotas[0].MaxQuotaValue)
                    new_used_quota = int(ref_quota.Quotas[0].UsedQuotaValue)
                    break
            assert new_max_quota == max_quota
            assert new_used_quota == 20
        finally:
            if sg_id:
                self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)

    def test_T1916_check_volume_limit(self):
        ret = self.a1_r1.icu.ReadQuotas(QuotaNames=['volume_limit'])

        used = ret.response.ReferenceQuota[0].Quotas[0].UsedQuotaValue
        limit = ret.response.ReferenceQuota[0].Quotas[0].MaxQuotaValue

        vol_list = []

        while used < limit:
            ret = self.a1_r1.fcu.CreateVolume(AvailabilityZone=self.a1_r1._config.region.az_name, Size='10')
            vol_list.append(ret.response.volumeId)
            used += 1
        wait_volumes_state(osc_sdk=self.a1_r1, state='available', volume_id_list=vol_list, wait_time=4)

        ret = self.a1_r1.icu.ReadQuotas(QuotaNames=['volume_limit'])
        assert ret.response.ReferenceQuota[0].Quotas[0].UsedQuotaValue == limit

        try:
            self.a1_r1.fcu.CreateVolume(AvailabilityZone=self.a1_r1._config.region.az_name, Size='10')
            assert False, "limit must be exceeded"
        except OscApiException as error:
            assert_code(error, 400)
            assert error.error_code == "VolumeLimitExceeded"
            assert error.message.startswith("The limit has exceeded")
        finally:
            for vol in vol_list:
                ret = self.a1_r1.fcu.DeleteVolume(VolumeId=vol)
