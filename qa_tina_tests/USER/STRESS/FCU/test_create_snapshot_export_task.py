from pprint import pprint
import string
import time

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.error import group_errors, error_type
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_volumes, delete_buckets
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state, wait_snapshot_export_tasks_state


CALL_NUMBER = 50


@pytest.mark.region_synchro_osu
@pytest.mark.region_osu
class Test_create_snapshot_export_task(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'snapshot_export_limit': 10}
        super(Test_create_snapshot_export_task, cls).setup_class()
        cls.snap_ids = []
        cls.vol_ids = None
        try:
            _, cls.vol_ids = create_volumes(cls.a1_r1, state="available", count=CALL_NUMBER)
            for vol_id in cls.vol_ids:
                cls.snap_ids.append(cls.a1_r1.fcu.CreateSnapshot(VolumeId=vol_id).response.snapshotId)
            wait_snapshots_state(cls.a1_r1, cls.snap_ids, state="completed")
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.snap_ids:
                for snap_id in cls.snap_ids:
                    cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
                wait_snapshots_state(osc_sdk=cls.a1_r1, cleanup=True, snapshot_id_list=cls.snap_ids)
            if cls.vol_ids:
                delete_volumes(cls.a1_r1, cls.vol_ids)
        finally:
            super(Test_create_snapshot_export_task, cls).teardown_class()

    def test_T4689_export_snapshot_multi(self):

        start = time.time()
        call_number = 0
        errs = group_errors()
        bucket_names = []
        responses = []
        task_ids = []
        try:
            for i in range(CALL_NUMBER):
                try:
                    call_number += 1
                    bucket_name = id_generator(chars=string.ascii_lowercase)
                    ret = self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_ids[i],
                                                                  ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': bucket_name})
                    responses.append(ret.response.snapshotExportTask)
                    task_ids.append(ret.response.snapshotExportTask.snapshotExportTaskId)
                    bucket_names.append(bucket_name)
                except OscApiException as error:
                    errs.handle_api_exception(error)
                except OscTestException as error:
                    errs.add_unexpected_error(error, error_type.Create)

            end = time.time()
            pprint(task_ids)
            error_wait = False
            try:
                wait_snapshot_export_tasks_state(self.a1_r1, task_ids, state='completed')
            except:
                error_wait = True
            if error_wait:
                ret = self.a1_r1.fcu.DescribeSnapshotExportTasks(SnapshotExportTaskId=task_ids)
                states = {[task.state for task in ret.response.snapshotExportTaskSet]}
                pprint(states)
                for task in ret.response.snapshotExportTask:
                    if task.state != 'completed' or task.completion != '100':
                        pprint(task.display())
            print("*************")
            print("call number = {}".format(call_number))
            print('time = {}'.format(end - start))
            errs.print_errors()
            errs.assert_errors()
            assert not error_wait
        finally:
            delete_buckets(self.a1_r1, bucket_names)

    def test_T4690_export_snapshot_mono(self):

        start = time.time()
        call_number = 0
        errs = group_errors()
        bucket_names = []
        responses = []
        task_ids = []
        try:
            for _ in range(CALL_NUMBER):
                try:
                    call_number += 1
                    bucket_name = id_generator(chars=string.ascii_lowercase)
                    ret = self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_ids[0],
                                                                  ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': bucket_name})
                    responses.append(ret.response.snapshotExportTask)
                    task_ids.append(ret.response.snapshotExportTask.snapshotExportTaskId)
                    bucket_names.append(bucket_name)
                except OscApiException as error:
                    errs.handle_api_exception(error)
                except OscTestException as error:
                    errs.add_unexpected_error(error, error_type.Create)

            end = time.time()
            pprint(task_ids)
            error_wait = False
            try:
                wait_snapshot_export_tasks_state(self.a1_r1, task_ids, state='completed')
            except:
                error_wait = True
            if error_wait:
                ret = self.a1_r1.fcu.DescribeSnapshotExportTasks(SnapshotExportTaskId=task_ids)
                states = {[task.state for task in ret.response.snapshotExportTaskSet]}
                pprint(states)
                for task in ret.response.snapshotExportTask:
                    if task.state != 'completed' or task.completion != '100':
                        pprint(task.display())
            print("*************")
            print("call number = {}".format(call_number))
            print('time = {}'.format(end - start))
            errs.print_errors()
            errs.assert_errors()
            assert not error_wait
        finally:
            delete_buckets(self.a1_r1, bucket_names)
