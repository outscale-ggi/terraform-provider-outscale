import time
from string import ascii_lowercase
import pytest
from botocore.exceptions import ClientError

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.exceptions import OscTestException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state, wait_snapshots_state, wait_snapshot_export_tasks_state



@pytest.mark.region_storageservice
class Test_ImportSnapshot(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ImportSnapshot, cls).setup_class()
        # vdi et vdmk not supported
        cls.supported_snap_types = ['qcow2']
        cls.vol_id = None
        cls.snap_id = None
        cls.task_ids = []
        cls.bucket_name = None
        cls.has_setup_error = None
        try:
            # create volume
            ret = cls.a1_r1.fcu.CreateVolume(AvailabilityZone=cls.a1_r1.config.region.az_name, Size='1')
            cls.vol_id = ret.response.volumeId
            wait_volumes_state(osc_sdk=cls.a1_r1, state='available', volume_id_list=[cls.vol_id])
            # snapshot volume
            ret = cls.a1_r1.fcu.CreateSnapshot(VolumeId=cls.vol_id)
            cls.snap_id = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=cls.a1_r1, state='completed', snapshot_id_list=[cls.snap_id])
            # export snapshot
            cls.bucket_name = id_generator(prefix='snap', chars=ascii_lowercase)
            for format_type in cls.supported_snap_types:
                ret = cls.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=cls.snap_id,
                                                             ExportToOsu={'DiskImageFormat': format_type, 'OsuBucket': cls.bucket_name})
                task_id = ret.response.snapshotExportTask.snapshotExportTaskId
                cls.task_ids.append(task_id)
            try:
                wait_snapshot_export_tasks_state(osc_sdk=cls.a1_r1, state='completed', snapshot_export_task_id_list=cls.task_ids)
                if cls.a1_r1.config.region.name == 'cloudgouv-eu-west-1':
                    pytest.fail('Remove known error code')
            except AssertionError:
                if cls.a1_r1.config.region.name == 'cloudgouv-eu-west-1':
                    cls.has_setup_error = 'OPS-12804'
                else:
                    raise
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    @classmethod
    def teardown_class(cls):
        errors = []
        try:
            if cls.bucket_name:
                try:
                    k_list = cls.a1_r1.storageservice.list_objects(Bucket=cls.bucket_name)
                    if 'Contents' in list(k_list.keys()):
                        for k in k_list['Contents']:
                            cls.a1_r1.storageservice.delete_object(Bucket=cls.bucket_name, Key=k['Key'])
                    cls.a1_r1.storageservice.delete_bucket(Bucket=cls.bucket_name)
                except ClientError as error:
                    if error.response['Error']['Code'] == 'NoSuchBucket' and cls.has_setup_error:
                        print('No object found because we had an error in the export snapshot- returning empty')
                except Exception as error:
                    errors.append(error)
            if cls.snap_id:
                # remove snapshot
                cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=cls.snap_id)
                wait_snapshots_state(osc_sdk=cls.a1_r1, cleanup=True, snapshot_id_list=[cls.snap_id])
            if cls.vol_id:
                # remove volume
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.vol_id)
                wait_volumes_state(osc_sdk=cls.a1_r1, cleanup=True, volume_id_list=[cls.vol_id])
            if errors:
                raise OscTestException('Found {} errors while cleaning resources : \n{}'.format(len(errors), errors))
        finally:
            super(Test_ImportSnapshot, cls).teardown_class()

    def test_T1051_without_parameter(self):
        if self.has_setup_error:
            known_error(self.has_setup_error, 'Unexpected error during setup')
        try:
            self.a1_r1.fcu.ImportSnapshot()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: snapshotLocation')

    def test_T1052_without_url(self):
        if self.has_setup_error:
            known_error(self.has_setup_error, 'Unexpected error during setup')
        try:
            self.a1_r1.fcu.ImportSnapshot(snapshotSize=1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: snapshotLocation')

    def test_T1053_with_invalid_url_format(self):
        if self.has_setup_error:
            known_error(self.has_setup_error, 'Unexpected error during setup')
        try:
            self.a1_r1.fcu.ImportSnapshot(snapshotSize=1, snapshotLocation='foo', description='This is a snapshot test')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidURLFormat', 'Only HTTP or HTTPs URL are accepted: foo')

    def test_T1055_with_invalid_url_expired(self):
        if self.has_setup_error:
            known_error(self.has_setup_error, 'Unexpected error during setup')
        try:
            snap_id = None
            key = None
            k_list = self.a1_r1.storageservice.list_objects(Bucket=self.bucket_name)
            if 'Contents' in list(k_list.keys()):
                key = k_list['Contents'][0]['Key']
            else:
                assert False, "Key not found on storageservice"
            params = {'Bucket': self.bucket_name, 'Key': key}
            url = self.a1_r1.storageservice.generate_presigned_url(ClientMethod='get_object', Params=params, ExpiresIn=1)
            ret = self.a1_r1.fcu.DescribeSnapshots(SnapshotId=[self.snap_id])
            size = ret.response.snapshotSet[0].volumeSize
            gb_to_byte = int(size) * pow(1024, 3)
            # wait snapshot to expires
            time.sleep(2)
            ret = self.a1_r1.fcu.ImportSnapshot(description='This is a snapshot test', snapshotLocation=url, snapshotSize=gb_to_byte)
            snap_id = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='error', snapshot_id_list=[snap_id])
        finally:
            if snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)

    def test_T1054_with_invalid_url(self):
        if self.has_setup_error:
            known_error(self.has_setup_error, 'Unexpected error during setup')
        try:
            snap_id = None
            key = None
            k_list = self.a1_r1.storageservice.list_objects(Bucket=self.bucket_name)
            if 'Contents' in list(k_list.keys()):
                key = k_list['Contents'][0]['Key']
            else:
                assert False, "Key not found on storageservice"
            params = {'Bucket': self.bucket_name, 'Key': key}
            url = self.a1_r1.storageservice.generate_presigned_url(ClientMethod='get_object', Params=params, ExpiresIn=3600)
            invalid_url = url[:-1]
            ret = self.a1_r1.fcu.DescribeSnapshots(SnapshotId=[self.snap_id])
            size = ret.response.snapshotSet[0].volumeSize
            gb_to_byte = int(size) * pow(1024, 3)
            ret = self.a1_r1.fcu.ImportSnapshot(description='This is a snapshot test', snapshotLocation=invalid_url, snapshotSize=gb_to_byte)
            snap_id = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='error', snapshot_id_list=[snap_id])
        finally:
            if snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)

    def test_T1056_with_deleted_bucket(self):
        if self.has_setup_error:
            known_error(self.has_setup_error, 'Unexpected error during setup')
        task_id = None
        bucket_name = None
        snap_id = None
        key = None
        try:
            bucket_name = id_generator(prefix='t1056', chars=ascii_lowercase)
            # create snapshot export task
            ret = self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snap_id,
                                                          ExportToOsu={'DiskImageFormat': self.supported_snap_types[0], 'OsuBucket': bucket_name})
            task_id = ret.response.snapshotExportTask.snapshotExportTaskId
            # wait completion export task
            wait_snapshot_export_tasks_state(osc_sdk=self.a1_r1, state='completed', snapshot_export_task_id_list=[task_id])
            k_list = self.a1_r1.storageservice.list_objects(Bucket=bucket_name)
            if 'Contents' in list(k_list.keys()):
                key = k_list['Contents'][0]['Key']
            else:
                assert False, "Key not found on storageservice"
            params = {'Bucket': bucket_name, 'Key': key}
            url = self.a1_r1.storageservice.generate_presigned_url(ClientMethod='get_object', Params=params, ExpiresIn=3600)
            for k in k_list['Contents']:
                self.a1_r1.storageservice.delete_object(Bucket=bucket_name, Key=k['Key'])
            self.a1_r1.storageservice.delete_bucket(Bucket=bucket_name)
            bucket_name = None
            ret = self.a1_r1.fcu.DescribeSnapshots(SnapshotId=[self.snap_id])
            size = ret.response.snapshotSet[0].volumeSize
            gb_to_byte = int(size) * pow(1024, 3)
            ret = self.a1_r1.fcu.ImportSnapshot(description='This is a snapshot test', snapshotLocation=url, snapshotSize=gb_to_byte)
            snap_id = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='error', snapshot_id_list=[snap_id])
        finally:
            if snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            if bucket_name:
                k_list = self.a1_r1.storageservice.list_objects(Bucket=bucket_name)
                if 'Contents' in list(k_list.keys()):
                    for k in k_list['Contents']:
                        self.a1_r1.storageservice.delete_object(Bucket=bucket_name, Key=k['Key'])
                self.a1_r1.storageservice.delete_bucket(Bucket=bucket_name)

    def test_T1057_without_snapshot_size(self):
        if self.has_setup_error:
            known_error(self.has_setup_error, 'Unexpected error during setup')
        try:
            key = None
            k_list = self.a1_r1.storageservice.list_objects(Bucket=self.bucket_name)
            if 'Contents' in list(k_list.keys()):
                key = k_list['Contents'][0]['Key']
            else:
                assert False, "Key not found on storageservice"
            params = {'Bucket': self.bucket_name, 'Key': key}
            url = self.a1_r1.storageservice.generate_presigned_url(ClientMethod='get_object', Params=params, ExpiresIn=3600)
            self.a1_r1.fcu.ImportSnapshot(description='This is a snapshot test', snapshotLocation=url)
            assert False, 'ImportSnapshot should have failed'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: snapshotSize')


    def test_T1050_with_valid_params(self):
        if self.has_setup_error:
            known_error(self.has_setup_error, 'Unexpected error during setup')
        try:
            snap_id = None
            key = None
            k_list = self.a1_r1.storageservice.list_objects(Bucket=self.bucket_name)
            if 'Contents' in list(k_list.keys()):
                key = k_list['Contents'][0]['Key']
            else:
                assert False, "Key not found on storageservice"
            params = {'Bucket': self.bucket_name, 'Key': key}
            url = self.a1_r1.storageservice.generate_presigned_url(ClientMethod='get_object', Params=params, ExpiresIn=3600)
            ret = self.a1_r1.fcu.DescribeSnapshots(SnapshotId=[self.snap_id])
            size = ret.response.snapshotSet[0].volumeSize
            gb_to_byte = int(size) * pow(1024, 3)
            ret = self.a1_r1.fcu.ImportSnapshot(snapshotLocation=url, snapshotSize=gb_to_byte, description='This is a snapshot test')
            snap_id = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap_id])
        finally:
            if snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)

    def test_T1059_with_valid_format_description(self):
        if self.has_setup_error:
            known_error(self.has_setup_error, 'Unexpected error during setup')
        try:
            snap_id = None
            key = None
            k_list = self.a1_r1.storageservice.list_objects(Bucket=self.bucket_name)
            if 'Contents' in list(k_list.keys()):
                key = k_list['Contents'][0]['Key']
            else:
                assert False, "Key not found on storageservice"
            params = {'Bucket': self.bucket_name, 'Key': key}
            url = self.a1_r1.storageservice.generate_presigned_url(ClientMethod='get_object', Params=params, ExpiresIn=3600)
            ret = self.a1_r1.fcu.DescribeSnapshots(SnapshotId=[self.snap_id])
            size = ret.response.snapshotSet[0].volumeSize
            gb_to_byte = int(size) * pow(1024, 3)
            ret = self.a1_r1.fcu.ImportSnapshot(description='This is a snapshot test', snapshotLocation=url, snapshotSize=gb_to_byte)
            snap_id = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap_id])
        finally:
            if snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)

    def test_T1058_with_wrong_size(self):
        if self.has_setup_error:
            known_error(self.has_setup_error, 'Unexpected error during setup')
        try:
            snap_id = None
            key = None
            k_list = self.a1_r1.storageservice.list_objects(Bucket=self.bucket_name)
            if 'Contents' in list(k_list.keys()):
                key = k_list['Contents'][0]['Key']
            else:
                assert False, "Key not found on storageservice"
            params = {'Bucket': self.bucket_name, 'Key': key}
            url = self.a1_r1.storageservice.generate_presigned_url(ClientMethod='get_object', Params=params, ExpiresIn=3600)
            ret = self.a1_r1.fcu.DescribeSnapshots(SnapshotId=[self.snap_id])
            size = ret.response.snapshotSet[0].volumeSize
            gb_to_byte = size
            ret = self.a1_r1.fcu.ImportSnapshot(description='This is a snapshot test', snapshotLocation=url, snapshotSize=gb_to_byte)
            snap_id = ret.response.snapshotId
            try:
                self.a1_r1.fcu.ImportSnapshot(description='This is a snapshot test', snapshotLocation=url,
                                              snapshotSize=gb_to_byte)
                known_error('TINA-6150', 'Import snapshot with wrong size does not return an error ')
            except OscApiException:
                assert False, 'remove known error and add an assert error'
        finally:
            if snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)

    def test_T4505_without_description(self):
        if self.has_setup_error:
            known_error(self.has_setup_error, 'Unexpected error during setup')
        try:
            snap_id = None
            key = None
            k_list = self.a1_r1.storageservice.list_objects(Bucket=self.bucket_name)
            if 'Contents' in list(k_list.keys()):
                key = k_list['Contents'][0]['Key']
            else:
                assert False, "Key not found on storageservice"
            params = {'Bucket': self.bucket_name, 'Key': key}
            url = self.a1_r1.storageservice.generate_presigned_url(ClientMethod='get_object', Params=params, ExpiresIn=3600)
            ret = self.a1_r1.fcu.DescribeSnapshots(SnapshotId=[self.snap_id])
            size = ret.response.snapshotSet[0].volumeSize
            gb_to_byte = int(size) * pow(1024, 3)
            ret = self.a1_r1.fcu.ImportSnapshot(snapshotLocation=url, snapshotSize=gb_to_byte)
            snap_id = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap_id])
        finally:
            if snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
