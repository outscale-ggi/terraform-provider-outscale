import datetime
from time import sleep

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state


ACCOUNTING_DELTA = 60
class Test_update_volume(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_update_volume, cls).setup_class()
        cls.vol = None

    @classmethod
    def teardown_class(cls):
        super(Test_update_volume, cls).teardown_class()

    def test_T5341_billing_update_volume_io1(self):
        is_deleted = False
        dates = []
        initial_size = 5
        update_size = 10
        iops = 1000
        try:
            self.vol = self.a1_r1.oapi.CreateVolume(Size=initial_size, SubregionName=self.azs[0],
                                                    Iops=iops, VolumeType='io1').response.Volume
            dates.append(datetime.datetime.utcnow())
            wait_volumes_state(self.a1_r1, [self.vol.VolumeId], state='available')
            sleep(60)

            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=update_size)
            dates.append(datetime.datetime.utcnow())
            wait_volumes_state(self.a1_r1, [self.vol.VolumeId], state='available')
            sleep(120)

            self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol.VolumeId)
            dates.append(datetime.datetime.utcnow())
            wait_volumes_state(osc_sdk=self.a1_r1, cleanup=True, volume_id_list=[self.vol.VolumeId])
            is_deleted = True
            sleep(60)

            user_name = self.a1_r1.config.account.account_id
            ret = self.a1_r1.intel.accounting.find(owner=[user_name], orders=[('id', 'ASC')], operation='CreateVolume', limit=6,
                                                   instance=self.vol.VolumeId).response.result.results
            assert len(ret) == 6
            i = 0
            j = 0
            """
                i = 0,1 CreateVolume (0: Opening the Size event 5Go, 1: for IOPS) <-> j : 0
                i = 2,3 UpdateVolume (2: Closing the previous Size, 3: Update 10Go) <-> j : 1
                i = 4,5 DeleteVolume (4: Closing the Size, 5: for IOPS) <-> j : 2
            """
            for r in ret:
                assert r.is_correlated is True
                assert r.operation == 'CreateVolume'
                assert (r.type == 'BSU:VolumeIOPS:io1' if i in [1, 5] else r.type == 'BSU:VolumeUsage:io1')
                assert r.instance == self.vol.VolumeId
                assert abs(dates[j] - r.created.dt) <= datetime.timedelta(seconds=ACCOUNTING_DELTA)

                if i in [0, 1, 3]:
                    assert(r.closing) is False
                    assert(r.is_last) is False
                    if hasattr(r, 'value'):
                        if i == 0:
                            assert int(r.value) == initial_size * 2 ** 30
                        elif i == 1:
                            assert int(r.value) == iops
                        else:
                            assert int(r.value) == update_size * 2 ** 30
                else:
                    assert(r.closing) is True
                    assert(r.is_last) is True

                j = i-j
                i += 1
        finally:
            if not is_deleted:
                if self.vol:
                    self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol.VolumeId)
