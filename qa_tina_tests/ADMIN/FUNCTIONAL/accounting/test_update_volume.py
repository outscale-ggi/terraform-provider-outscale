import datetime

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state

ACCOUNTING_DELTA = 2

class Test_update_volume(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_update_volume, cls).setup_class()
        cls.vol = None

    @classmethod
    def teardown_class(cls):
        super(Test_update_volume, cls).teardown_class()

    def test_TXXX_billing_update_volume(self):
        is_deleted = False
        dates = []
        try:
            self.vol = self.a1_r1.oapi.CreateVolume(VolumeType='standard', Size=2,
                                                    SubregionName=self.azs[0]).response.Volume
            dates.append(datetime.datetime.now())
            wait_volumes_state(self.a1_r1, [self.vol.VolumeId], state='available')

            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=5)
            dates.append(datetime.datetime.now())
            wait_volumes_state(self.a1_r1, [self.vol.VolumeId], state='available')

            self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol.VolumeId)
            dates.append(datetime.datetime.now())
            wait_volumes_state(osc_sdk=self.a1_r1, cleanup=True, volume_id_list=[self.vol.VolumeId])
            is_deleted = True

            user_name = self.a1_r1.config.account.account_id
            ret = self.a1_r1.intel.accounting.find(owner=[user_name], operation='CreateVolume', limit=6,
                                                   instance=self.vol.VolumeId).response.result.results
            #assert len(ret) == 3
            i = 0
            for r in ret:
                assert r.is_correlated is True
                assert r.operation == 'CreateVolume'
                assert r.type == 'BSU:VolumeUsage:standard'
                assert r.instance == self.vol.VolumeId

                if hasattr(r, 'value'):
                    if i == 1:
                        assert int(r.value) == 5 * 2 ** 30
                        assert r.created.dt.strftime("%Y-%m-%d %H:%M:%S") == dates[i].strftime("%Y-%m-%d %H:%M:%S")
                    if i == 3:
                        assert int(r.value) == 2 * 2 ** 30
                        assert r.created.dt.strftime("%Y-%m-%d %H:%M:%S") == dates[0].strftime("%Y-%m-%d %H:%M:%S")
                if i in [0, 2]:
                    assert(r.closing) is True
                    assert(r.is_last) is True
                if i in [1, 3]:
                    assert(r.closing) is False
                    assert(r.is_last) is False
                i = i+1
        finally:
            if not is_deleted:
                self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol.VolumeId)
