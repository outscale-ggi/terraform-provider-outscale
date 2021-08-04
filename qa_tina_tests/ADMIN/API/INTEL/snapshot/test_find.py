from qa_tina_tools.test_base import OscTinaTest


class Test_find(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_find, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_find, cls).teardown_class()

    def test_T2993_find_snapshot_by_mount_point(self):
        snap_count = 0
        ret = self.a1_r1.intel.storage.find_shards()
        for mount_point in ret.response.result:
            snap_per_mp = self.a1_r1.intel.snapshot.find(mount_points=mount_point.mount_point)
            snap_count += len(snap_per_mp.response.result)
        # all_snap = self.a1_r1.intel.snapshot.find()
        # assert snap_count == len(all_snap.response.result), 'Error on snapshot count'
