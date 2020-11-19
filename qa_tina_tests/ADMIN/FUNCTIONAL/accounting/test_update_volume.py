from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state

class Test_update_volume(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_update_volume, cls).setup_class()
        cls.vol = None

    @classmethod
    def teardown_class(cls):
        super(Test_update_volume, cls).teardown_class()

    def test_TXXX_billing_update_volume(self):
        self.vol = self.a1_r1.oapi.CreateVolume(VolumeType='standard', Size=2,
                                                SubregionName=self.azs[0]).response.Volume
        wait_volumes_state(self.a1_r1, [self.vol.VolumeId], state='available')

        self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=5)
        wait_volumes_state(self.a1_r1, [self.vol.VolumeId], state='available')

        self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol.VolumeId)
        wait_volumes_state(self.a1_r1, [self.vol.VolumeId], state='deleting')

        user_name = self.a1_r1.config.account.account_id
        ret = self.a1_r1.intel.accounting.find(owner=[user_name], operation='CreateVolume', limit=6,
                                               orders=[('id', 'DESC')]).response.result.results

        assert len(ret) == 6

        i = 0
        for r in ret:
            assert r.is_correlated is True
            assert r.operation == 'CreateVolume'
            assert r.type == 'BSU:VolumeUsage:standard'
            if hasattr(r, 'value'):
                if i in [1,5]:
                    assert int(r.value) == 5 * 2 ** 30
                if i == 3:
                    assert int(r.value) == 2 * 2 ** 30
            if i in [0, 2, 4]:
                assert(r.closing) is True
                assert(r.is_last) is True
            if i in [1, 3, 5]:
                assert(r.closing) is False
                assert(r.is_last) is False
            i = i+1
