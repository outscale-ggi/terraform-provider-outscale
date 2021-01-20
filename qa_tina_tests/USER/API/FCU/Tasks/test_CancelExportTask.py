# -*- coding:utf-8 -*-
from string import ascii_lowercase

from qa_tina_tools.tools.tina.delete_tools import delete_instances

from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, BLOCK_DEVICE_MAPPING, VOLUME_ID, EBS

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state, wait_snapshots_state, \
    wait_snapshot_export_tasks_state


class Test_CancelExportTask(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CancelExportTask, cls).setup_class()
        cls.supported_snap_types = ['qcow2']
        cls.vol_id = None
        cls.snap_id = None
        cls.task_ids = []
        cls.bucket_name = None
        cls.has_setup_error = None
        try:
            # create volume
            cls.inst_info = create_instances(cls.a1_r1)
            cls.vol_id_boot = cls.inst_info[INSTANCE_SET][0][BLOCK_DEVICE_MAPPING][0][EBS][VOLUME_ID]
            ret = cls.a1_r1.fcu.CreateVolume(AvailabilityZone=cls.a1_r1.config.region.az_name, Size='1')
            cls.vol_id = ret.response.volumeId
            wait_volumes_state(osc_sdk=cls.a1_r1, state='available', volume_id_list=[cls.vol_id])
            wait_volumes_state(osc_sdk=cls.a1_r1, state='in-use', volume_id_list=[cls.vol_id_boot])
            # snapshot volume
            ret = cls.a1_r1.fcu.CreateSnapshot(VolumeId=cls.vol_id)
            cls.snap_id = ret.response.snapshotId
            ret = cls.a1_r1.fcu.CreateSnapshot(VolumeId=cls.vol_id_boot)
            cls.snap_id_boot = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=cls.a1_r1, state='completed', snapshot_id_list=[cls.snap_id, cls.snap_id_boot])
            # export snapshot
            cls.bucket_name = id_generator(prefix='snap', chars=ascii_lowercase)
            for e in cls.supported_snap_types:
                ret = cls.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=cls.snap_id,
                                                             ExportToOsu={'DiskImageFormat': e,
                                                                          'OsuBucket': cls.bucket_name})
                task_id = ret.response.snapshotExportTask.snapshotExportTaskId
                cls.task_ids.append(task_id)
                wait_snapshot_export_tasks_state(osc_sdk=cls.a1_r1, state='completed',
                                                 snapshot_export_task_id_list=cls.task_ids)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.bucket_name:
                try:
                    k_list = cls.a1_r1.storageservice.list_objects(Bucket=cls.bucket_name)
                    if 'Contents' in list(k_list.keys()):
                        for k in k_list['Contents']:
                            cls.a1_r1.storageservice.delete_object(Bucket=cls.bucket_name, Key=k['Key'])
                    cls.a1_r1.storageservice.delete_bucket(Bucket=cls.bucket_name)
                except:
                    pass
            if cls.snap_id:
                # remove snapshot
                cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=cls.snap_id)
                wait_snapshots_state(osc_sdk=cls.a1_r1, cleanup=True, snapshot_id_list=[cls.snap_id])

            if cls.snap_id_boot:
                # remove snapshot
                cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=cls.snap_id_boot)
                wait_snapshots_state(osc_sdk=cls.a1_r1, cleanup=True, snapshot_id_list=[cls.snap_id_boot])
            if cls.vol_id:
                # remove volume
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.vol_id)
                wait_volumes_state(osc_sdk=cls.a1_r1, cleanup=True, volume_id_list=[cls.vol_id])
            if cls.inst_info:
                delete_instances(cls.a1_r1, [cls.inst_info])

        finally:
            super(Test_CancelExportTask, cls).teardown_class()

    def test_T5456_valid_export_task_id(self):
        try:
            self.a1_r1.fcu.CancelExportTask(ExportTaskId=self.task_ids[0])
            known_error('TINA-6158', 'cancel of a completed export snapshot task does not return an error')
        except OscApiException as error:
            assert False, 'remove known error'
            assert_error(error, ' ', ' ', ' ')

    def test_T5457_check_cancelled_state(self):
        bucket_name = id_generator(prefix='snap', chars=ascii_lowercase)
        ret = self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id_boot,
                                                      ExportToOsu={'DiskImageFormat': 'qcow2',
                                                                   'OsuBucket': bucket_name})
        task_id = ret.response.snapshotExportTask.snapshotExportTaskId
        self.a1_r1.fcu.CancelExportTask(ExportTaskId=task_id)
        wait_snapshot_export_tasks_state(osc_sdk=self.a1_r1, state='cancelled',
                                         snapshot_export_task_id_list=[task_id])
