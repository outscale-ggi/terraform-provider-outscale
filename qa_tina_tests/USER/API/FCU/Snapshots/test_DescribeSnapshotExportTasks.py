import pytest
from string import ascii_lowercase
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.misc import id_generator, assert_error
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state, wait_snapshot_export_tasks_state


@pytest.mark.region_osu
class Test_DescribeSnapshotExportTasks(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeSnapshotExportTasks, cls).setup_class()
        vol_id = None
        snap_id = None
        cls.task_ids = []
        cls.bucket_name = None
        try:
            cls.logger.debug("Export 3 snapshots to OSU with account 1")
            # create volume
            ret = cls.a1_r1.fcu.CreateVolume(AvailabilityZone=cls.a1_r1._config.region.az_name, Size='10')
            vol_id = ret.response.volumeId
            wait_volumes_state(osc_sdk=cls.a1_r1, state='available', volume_id_list=[vol_id])
            # snapshot volume
            ret = cls.a1_r1.fcu.CreateSnapshot(VolumeId=vol_id)
            snap_id = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=cls.a1_r1, state='completed', snapshot_id_list=[snap_id])
            # export snapshot
            cls.bucket_name = id_generator(prefix='snap_', chars=ascii_lowercase)
            for _ in range(3):
                ret = cls.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=snap_id, ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': cls.bucket_name})
                task_id = ret.response.snapshotExportTask.snapshotExportTaskId
                cls.task_ids.append(task_id)
            wait_snapshot_export_tasks_state(osc_sdk=cls.a1_r1, state='completed', snapshot_export_task_id_list=cls.task_ids)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise
        finally:
            if snap_id:
                # remove snapshot
                ret = cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
                wait_snapshots_state(osc_sdk=cls.a1_r1, cleanup=True, snapshot_id_list=[snap_id])
            if vol_id:
                # remove volume
                ret = cls.a1_r1.fcu.DeleteVolume(VolumeId=vol_id)
                wait_volumes_state(osc_sdk=cls.a1_r1, cleanup=True, volume_id_list=[vol_id])

    @classmethod
    def teardown_class(cls):
        try:
            if cls.bucket_name:
                cls.logger.debug("Remove snapshot on OSU")
                k_list = cls.a1_r1.osu.list_objects(Bucket=cls.bucket_name)
                if 'Contents' in list(k_list.keys()):
                    for k in k_list['Contents']:
                        cls.a1_r1.osu.delete_object(Bucket=cls.bucket_name, Key=k['Key'])
                cls.a1_r1.osu.delete_bucket(Bucket=cls.bucket_name)
        finally:
            super(Test_DescribeSnapshotExportTasks, cls).teardown_class()

    def test_T1039_without_param(self):
        ret = self.a1_r1.fcu.DescribeSnapshotExportTasks()
        assert len(ret.response.snapshotExportTaskSet) >= 3
        for task_id in self.task_ids:
            assert task_id in [t.snapshotExportTaskId for t in ret.response.snapshotExportTaskSet]

    def test_T1040_with_snapshot_export_task_id(self):
        ret = self.a1_r1.fcu.DescribeSnapshotExportTasks(SnapshotExportTaskId=[self.task_ids[0]])
        assert len(ret.response.snapshotExportTaskSet) == 1
        assert ret.response.snapshotExportTaskSet[0].snapshotExportTaskId == self.task_ids[0]

    def test_T1041_with_multiple_snapshot_export_task_id(self):
        ret = self.a1_r1.fcu.DescribeSnapshotExportTasks(SnapshotExportTaskId=[self.task_ids[0], self.task_ids[1]])
        assert len(ret.response.snapshotExportTaskSet) == 2

    def test_T1042_with_invalid_snapshot_export_task_id(self):
        try:
            self.a1_r1.fcu.DescribeSnapshotExportTasks(SnapshotExportTaskId=['snap-export-xxxxxxxx'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshotExportTaskID.NotFound', "The snapshot export task ID 'snap-export-xxxxxxxx' does not exist")

    def test_T1043_with_snapshot_export_task_id_from_another_account(self):
        try:
            self.a2_r1.fcu.DescribeSnapshotExportTasks(SnapshotExportTaskId=[self.task_ids[0]])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshotExportTaskID.NotFound',
                        "The snapshot export task ID '{}' does not exist".format(self.task_ids[0]))

    def test_T3244_from_another_account(self):
        ret = self.a2_r1.fcu.DescribeSnapshotExportTasks()
        assert not ret.response.snapshotExportTaskSet
