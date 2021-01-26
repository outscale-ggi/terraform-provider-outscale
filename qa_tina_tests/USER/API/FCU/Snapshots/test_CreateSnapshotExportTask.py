# pylint: disable=missing-docstring

from string import ascii_lowercase

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_volumes, delete_buckets
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state, wait_snapshot_export_tasks_state


class Test_CreateSnapshotExportTask(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateSnapshotExportTask, cls).setup_class()
        cls.vol_id = None
        cls.snap_id = None
        cls.bucket_name = None
        try:
            _, [cls.vol_id] = create_volumes(cls.a1_r1, state='available')
            cls.snap_id = cls.a1_r1.fcu.CreateSnapshot(VolumeId=cls.vol_id).response.snapshotId
            wait_snapshots_state(osc_sdk=cls.a1_r1, state='completed', snapshot_id_list=[cls.snap_id])
        except:
            # pylint: disable=bare-except
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.snap_id:
                cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=cls.snap_id)
                wait_snapshots_state(osc_sdk=cls.a1_r1, cleanup=True, snapshot_id_list=[cls.snap_id])
            if cls.vol_id:
                delete_volumes(cls.a1_r1, [cls.vol_id])
        finally:
            super(Test_CreateSnapshotExportTask, cls).teardown_class()

    def setup_method(self, method):
        super(Test_CreateSnapshotExportTask, self).setup_method(method)
        self.bucket_name = id_generator(prefix='snap', chars=ascii_lowercase)
        try:
            pass
        except:
            # pylint: disable=bare-except
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.a1_r1.config.region.get_info(constants.STORAGESERVICE) in ['oos', 'osu']:
                delete_buckets(self.a1_r1, [self.bucket_name])
                delete_buckets(self.a2_r1, [self.bucket_name])
        finally:
            super(Test_CreateSnapshotExportTask, self).teardown_method(method)

    @pytest.mark.region_storageservice
    def test_T1019_valid_parameters(self):
        ret = self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id, ExportToOsu={'DiskImageFormat': 'qcow2',
                                                                                            'OsuBucket': self.bucket_name})
        task_id = ret.response.snapshotExportTask.snapshotExportTaskId
        assert ret.response.snapshotExportTask.snapshotExportTaskId.startswith('snap-export-')
        assert ret.response.snapshotExportTask.state == 'pending'
        assert ret.response.snapshotExportTask.completion == '0'
        assert ret.response.snapshotExportTask.snapshotExport.snapshotId == self.snap_id
        assert ret.response.snapshotExportTask.exportToOsu.diskImageFormat == 'qcow2'
        assert ret.response.snapshotExportTask.exportToOsu.osuBucket == self.bucket_name
        wait_snapshot_export_tasks_state(osc_sdk=self.a1_r1, state='completed', snapshot_export_task_id_list=[task_id])
        k_list = self.a1_r1.storageservice.list_objects(Bucket=self.bucket_name)['Contents']
        assert len(k_list) == 1
        assert k_list[0]['Size'] > 0
        if '{}-{}.qcow2.gz'.format(self.snap_id, task_id.split('-')[2]) == k_list[0]['Key']:
            known_error('TINA-4948', 'Wrong object name on OSU after Snapshot export')
        assert False, "Remove known error"
        assert '{}.qcow2.gz'.format(task_id) == k_list[0]['Key']

    def test_T1021_without_snapshot_id(self):
        try:
            self.a1_r1.fcu.CreateSnapshotExportTask(ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': self.bucket_name})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: SnapshotId')

    def test_T1025_without_disk_image_format(self):
        try:
            self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id, ExportToOsu={'OsuBucket': self.bucket_name})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: DiskImageFormat')

    def test_T1027_without_osu_bucket(self):
        try:
            self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id, ExportToOsu={'DiskImageFormat': 'qcow2'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: OsuBucket')

    @pytest.mark.tag_sec_confidentiality
    def test_T1023_with_snapshot_id_from_another_account(self):
        try:
            self.a2_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id, ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': self.bucket_name})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshot.NotFound',
                         'The Snapshot ID does not exist: {}, for account: {}'.format(self.snap_id, self.a2_r1.config.account.account_id))

    @pytest.mark.region_storageservice
    def test_T3890_with_shared_snapshot_id(self):
        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=self.snap_id,
                                               CreateVolumePermission={'Add': [{'UserId': self.a2_r1.config.account.account_id}]})
        ret = self.a2_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id, ExportToOsu={'DiskImageFormat': 'qcow2',
                                                                                            'OsuBucket': self.bucket_name})
        task_id = ret.response.snapshotExportTask.snapshotExportTaskId
        self.logger.debug(ret.response.display())
        wait_snapshot_export_tasks_state(osc_sdk=self.a2_r1, state='completed', snapshot_export_task_id_list=[task_id])
        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=self.snap_id,
                                               CreateVolumePermission={'Remove': [{'UserId': self.a2_r1.config.account.account_id}]})

    def test_T1022_with_invalid_snapshot_id(self):
        try:
            self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId='foo', ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': self.bucket_name})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshotID.Malformed',
                         'Invalid ID received: foo. Expected format: snap-')

    def test_T4527_with_invalid_snapshot_id_prefix_snap(self):
        try:
            self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId='snap-123456', ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': self.bucket_name})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshotID.Malformed',
                         'Invalid ID received: snap-123456')

    def test_T1026_with_invalid_disk_image_format(self):
        disk_format_list = ['foo', 'vdi', 'vmdk']
        for disk_format in disk_format_list:
            try:
                self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id, ExportToOsu={'DiskImageFormat': disk_format,
                                                                                              'OsuBucket': self.bucket_name})
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'InvalidParameterValue', "Value of parameter \'DiskFormat\' is not valid: {}. Supported values: qcow2, raw".format(disk_format))

    def test_T1028_with_invalid_osu_bucket(self):
        try:
            self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id, ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': "FOO"})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Value of parameter 'OsuBucket' must be lowercase. Received: FOO")

    @pytest.mark.region_storageservice
    def test_T3891_with_existing_osu_bucket(self):
        self.a1_r1.storageservice.create_bucket(Bucket=self.bucket_name)
        ret = self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id, ExportToOsu={'DiskImageFormat': 'qcow2',
                                                                                            'OsuBucket': self.bucket_name})
        task_id = ret.response.snapshotExportTask.snapshotExportTaskId
        assert ret.response.snapshotExportTask.exportToOsu.osuBucket == self.bucket_name
        wait_snapshot_export_tasks_state(osc_sdk=self.a1_r1, state='completed', snapshot_export_task_id_list=[task_id])
        k_list = self.a1_r1.storageservice.list_objects(Bucket=self.bucket_name)['Contents']
        assert len(k_list) == 1
        assert k_list[0]['Size'] > 0
        if '{}-{}.qcow2.gz'.format(self.snap_id, task_id.split('-')[2]) == k_list[0]['Key']:
            known_error('TINA-4948', 'Wrong object name on OSU after Snapshot export')
        assert False, "Remove known error"
        assert '{}.qcow2.gz'.format(task_id) == k_list[0]['Key']

    @pytest.mark.region_storageservice
    def test_T3892_with_osu_key(self):
        ret = self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id, ExportToOsu={'DiskImageFormat': 'qcow2',
                                                                                            'OsuBucket': self.bucket_name, 'OsuKey': 'osu_key'})
        task_id = ret.response.snapshotExportTask.snapshotExportTaskId
        assert not hasattr(ret.response.snapshotExportTask.exportToOsu, 'osuKey')
        wait_snapshot_export_tasks_state(osc_sdk=self.a1_r1, state='completed', snapshot_export_task_id_list=[task_id])
        k_list = self.a1_r1.storageservice.list_objects(Bucket=self.bucket_name)['Contents']
        assert len(k_list) == 1
        assert k_list[0]['Size'] > 0
        if '{}-{}.qcow2.gz'.format(self.snap_id, task_id.split('-')[2]) == k_list[0]['Key']:
            known_error('TINA-4948', 'Wrong object name on OSU after Snapshot export')
        assert False, "Remove known error"
        # OsuKey not supported by Tina
        assert '{}.qcow2.gz'.format(task_id) == k_list[0]['Key']

    @pytest.mark.region_storageservice
    def test_T3893_with_osu_prefix(self):
        ret = self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id, ExportToOsu={'DiskImageFormat': 'qcow2',
                                                                                            'OsuBucket': self.bucket_name,
                                                                                            'OsuPrefix': 'osu_prefix-'})
        task_id = ret.response.snapshotExportTask.snapshotExportTaskId
        assert hasattr(ret.response.snapshotExportTask.exportToOsu, 'osuPrefix')
        wait_snapshot_export_tasks_state(osc_sdk=self.a1_r1, state='completed', snapshot_export_task_id_list=[task_id])
        k_list = self.a1_r1.storageservice.list_objects(Bucket=self.bucket_name)['Contents']
        assert len(k_list) == 1
        assert k_list[0]['Size'] > 0
        if 'osu_prefix-{}-{}.qcow2.gz'.format(self.snap_id, task_id.split('-')[2]) == k_list[0]['Key']:
            known_error('TINA-4948', 'Wrong object name on OSU after Snapshot export')
        assert False, "Remove known error"
        assert 'osu_prefix-{}.qcow2.gz'.format(task_id) == k_list[0]['Key']

    @pytest.mark.region_storageservice
    def test_T3894_with_ak_sk(self):
        ret = self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id, ExportToOsu={'DiskImageFormat': 'qcow2',
                                                                                            'OsuBucket': self.bucket_name,
                                                                                            'aksk':{'AccessKey': self.a1_r1.config.account.ak,
                                                                                                    'SecretKey': self.a1_r1.config.account.sk}})
        task_id = ret.response.snapshotExportTask.snapshotExportTaskId
        wait_snapshot_export_tasks_state(osc_sdk=self.a1_r1, state='completed', snapshot_export_task_id_list=[task_id])

    # def test_T0000_with_invalid_osu_key(self):
        # OsuKey not supported by Tina

    def test_T3895_with_invalid_osu_prefix(self):
        known_error('TINA-4950', 'SnapExport: call in error with invalid OsuPrefix')
        try:
            ret = self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id, ExportToOsu={'DiskImageFormat': 'qcow2',
                                                                                                'OsuBucket': self.bucket_name,
                                                                                                'OsuPrefix': '/foo%bar&'})
            self.logger.debug(ret.response.display())
        #    task_id = ret.response.snapshotExportTask.snapshotExportTaskId
        #    wait_snapshot_export_tasks_state(osc_sdk=self.a1_r1, state='completed',
        #                                     snapshot_export_task_id_list=[task_id])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshot.NotFound',
                         'The Snapshot ID does not exist: foo, for account: {}'.format(self.a1_r1.config.account.account_id))

    @pytest.mark.region_storageservice
    def test_T3896_with_invalid_ak_sk(self):
        ret = self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id, ExportToOsu={'DiskImageFormat': 'qcow2',
                                                                                            'OsuBucket': self.bucket_name,
                                                                                            'aksk':{'AccessKey': 'foo', 'SecretKey': 'bar'}})
        task_id = ret.response.snapshotExportTask.snapshotExportTaskId
        try:
            wait_snapshot_export_tasks_state(osc_sdk=self.a1_r1, state='failed', snapshot_export_task_id_list=[task_id])
            assert False, 'Remove known error'
        except AssertionError as error:
            known_error('TINA-6147', 'Create export snapshot task with invalid ak/sk should have the failed state')
        ret = self.a1_r1.fcu.DescribeSnapshotExportTasks(SnapshotExportTaskId=[task_id])
        assert ret.response.snapshotExportTaskSet[0].statusMessage.startswith('Error accessing bucket ' + \
                                                                              '{}: S3ResponseError: 403 Forbidden\n'.format(self.bucket_name) + \
                                                                              '<?xml version="1.0" encoding="UTF-8"?>' + \
                                                                              '<Error><Code>InvalidAccessKeyId</Code>')
