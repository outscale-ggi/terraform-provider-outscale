import pytest

from qa_test_tools.misc import assert_dry_run
from qa_tina_tests.USER.API.OAPI.Snapshot.Snapshot import Snapshot


@pytest.mark.region_storageservice
class Test_ReadSnapshotExportTasks(Snapshot):

    @classmethod
    def setup_class(cls):
        super(Test_ReadSnapshotExportTasks, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ReadSnapshotExportTasks, cls).teardown_class()

    def test_T3005_empty_filters(self):
        snapshot_id = self.a1_r1.oapi.CreateSnapshot(VolumeId=self.volume_id1).response.Snapshot.SnapshotId
        try:
            self.a1_r1.oapi.CreateSnapshotExportTask(SnapshotId=snapshot_id,
                                                     OsuExport={'DiskImageFormat': 'qcow2',
                                                                'OsuBucket': 'snap-569',
                                                                'OsuPrefix': '/foo%bar&'})
            ret = self.a1_r1.oapi.ReadSnapshotExportTasks()
            for task in ret.response.SnapshotExportTasks:
                if task.SnapshotId == snapshot_id:
                    assert task.OsuExport.OsuPrefix == '/foo%bar&'
            ret.check_response()
        finally:
            if snapshot_id:
                self.a1_r1.oapi.DeleteSnapshot(SnapshotId=snapshot_id)

    def test_T3006_valid_param_dry_run(self):
        ret = self.a1_r1.oapi.ReadSnapshotExportTasks(DryRun=True)
        assert_dry_run(ret)

    def test_T3010_invalid_filters_task_ids(self):
        ret = self.a1_r1.oapi.ReadSnapshotExportTasks(Filters={"TaskIds": ['abcd']})
        ret.check_response()

    def test_T3011_malformed_filters_task_ids(self):
        ret = self.a1_r1.oapi.ReadSnapshotExportTasks(Filters={"TaskIds": ['snap-export-123456']})
        ret.check_response()

    def test_T3012_unknown_filters_task_ids(self):
        ret = self.a1_r1.oapi.ReadSnapshotExportTasks(Filters={"TaskIds": ['snap-export-12345678']})
        ret.check_response()

    @pytest.mark.tag_sec_confidentiality
    def test_T3438_with_other_account(self):
        ret = self.a2_r1.oapi.ReadSnapshotExportTasks().response
        assert not ret.SnapshotExportTasks
