from qa_test_tools.test_base import OscTestSuite


VOLUME_NUMBER = 10


class Test_find(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vol_ids = []
        super(Test_find, cls).setup_class()
        try:
            for _ in range(VOLUME_NUMBER):
                resp = cls.a1_r1.oapi.CreateVolume(SubregionName=cls.a1_r1.config.region.az_name, Size=10).response
                cls.vol_ids.append(resp.Volume.VolumeId)
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            for vol_id in cls.vol_ids:
                try:
                    cls.a1_r1.oapi.DeleteVolume(VolumeId=vol_id)
                except:
                    print('Could not delete volume')
        finally:
            super(Test_find, cls).teardown_class()

    def test_T5071_with_order_id(self):
        resp = self.a1_r1.intel.volume.find(limit=20, orders=[('id', 'ASC')], owner=self.a1_r1.config.account.account_id).response
        vol_ids = [vol.id for vol in resp.result.results]
        assert len(vol_ids) == VOLUME_NUMBER
        assert sorted(vol_ids) == vol_ids
        assert sorted(self.vol_ids) == sorted(vol_ids)
