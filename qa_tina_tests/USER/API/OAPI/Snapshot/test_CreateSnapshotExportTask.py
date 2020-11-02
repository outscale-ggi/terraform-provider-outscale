from qa_test_tools.test_base import known_error

from qa_tina_tests.USER.API.OAPI.Snapshot.Snapshot import Snapshot
import pytest
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state


class Test_CreateSnapshotExportTask(Snapshot):

    @classmethod
    def setup_class(cls):
        super(Test_CreateSnapshotExportTask, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateSnapshotExportTask, cls).teardown_class()

    @pytest.mark.region_storageservice
    def test_T4675_valid_param(self):
        snapshot_id = self.a1_r1.oapi.CreateSnapshot(VolumeId=self.volume_id1).response.Snapshot.SnapshotId
        wait_snapshots_state(self.a1_r1, [snapshot_id], state='completed')
        try:
            ret = self.a1_r1.oapi.CreateSnapshotExportTask(SnapshotId=snapshot_id, OsuExport={'DiskImageFormat': 'qcow2', 'OsuBucket':'snap-569'})
            if not hasattr(ret.response, 'SnapshotExportTask'):
                known_error('GTW-1488', 'CreateSnapshotExportTask does not return SnapshotExportTask in response')
            else:
                assert False, 'Remove known error'
        finally:
            if snapshot_id:
                self.a1_r1.oapi.DeleteSnapshot(SnapshotId=snapshot_id)
