from qa_tina_tests.USER.API.OAPI.Snapshot.Snapshot import Snapshot


class Test_CreateSnapshotExportTask(Snapshot):

    @classmethod
    def setup_class(cls):
        super(Test_CreateSnapshotExportTask, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateSnapshotExportTask, cls).teardown_class()

    def test_T4675_valid_param(self):
        snapshot = self.a1_r1.oapi.CreateSnapshot(VolumeId=self.volume_id1).response.Snapshot
        try:
            self.a1_r1.oapi.CreateSnapshotExportTask(SnapshotId=snapshot.SnapshotId, OsuExport={'DiskImageFormat': 'qcow2', 'OsuBucket':'snap-569'})
        finally:
            if snapshot:
                self.a1_r1.oapi.DeleteSnapshot(SnapshotId=snapshot.SnapshotId)
