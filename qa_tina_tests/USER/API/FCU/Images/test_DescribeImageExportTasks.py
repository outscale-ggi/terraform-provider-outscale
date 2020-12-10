from string import ascii_lowercase

import pytest

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances, create_image
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_image_export_tasks_state

NUM_EXPORT_TASK = 2

@pytest.mark.region_storageservice
class Test_DescribeImageExportTasks(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'image_export_limit': NUM_EXPORT_TASK}
        cls.image_ids = []
        cls.inst_info = None
        cls.image_exp_ids = []
        cls.bucket_names = []
        super(Test_DescribeImageExportTasks, cls).setup_class()
        try:
            cls.inst_info = create_instances(cls.a1_r1)
            cls.inst_id = cls.inst_info[INSTANCE_ID_LIST][0]

            for _ in range(NUM_EXPORT_TASK):
                ret , image_id = create_image(cls.a1_r1, cls.inst_id, state='available')
                cls.image_ids.append(image_id)
                bucket_name = id_generator(prefix='bucket', chars=ascii_lowercase)
                cls.bucket_names.append(bucket_name)
                image_export = cls.a1_r1.fcu.CreateImageExportTask(ImageId=image_id,ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': bucket_name})
                image_export_id = image_export.response.imageExportTask.imageExportTaskId
                cls.image_exp_ids.append(image_export_id)

        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            for bucket_name in cls.bucket_names:
                if bucket_name:
                    k_list = cls.a1_r1.storageservice.list_objects(Bucket=bucket_name)
                    if 'Contents' in list(k_list.keys()):
                        for k in k_list['Contents']:
                            cls.a1_r1.storageservice.delete_object(Bucket=bucket_name, Key=k['Key'])
                    cls.a1_r1.storageservice.delete_bucket(Bucket=bucket_name)
            for image_id in cls.image_ids:
                cls.a1_r1.fcu.DeregisterImage(ImageId=image_id)
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_DescribeImageExportTasks, cls).teardown_class()

    def test_T5356_without_params(self):
        ret = self.a1_r1.fcu.DescribeImageExportTasks().response
        assert ret.requestId
        assert len(ret.imageExportTaskSet) >= 2

    def test_T5357_with_image_export_task_id(self):
        ret = self.a1_r1.fcu.DescribeImageExportTasks(imageExportTaskId=[self.image_exp_ids[0]]).response.imageExportTaskSet
        if len(ret) != 1:
            known_error('TINA-6064', 'DescribeImageExportTasks')
        assert False, 'Remove known error code'
        wait_image_export_tasks_state(osc_sdk=self.a1_r1, state='completed',
                                      image_export_task_id_list=[ret[0].imageExportTaskId])
        assert ret.state == 'completed'
        assert ret.exportToOsu.diskImageFormat == 'qcow2'
        assert ret.exportToOsu.osuBucket == self.bucket_names[0]
        assert ret.imageExport.imageId == self.image_ids[0]

    def test_T5358_with_image_export_task_ids(self):
        ret = self.a1_r1.fcu.DescribeImageExportTasks(imageExportTaskId=[self.image_exp_ids]).response
        if len(ret.imageExportTaskSet) != 2:
            known_error('TINA-6064', 'DescribeImageExportTasks')
        assert False, 'Remove known error code'
        wait_image_export_tasks_state(osc_sdk=self.a1_r1, state='completed',
                                      image_export_task_id_list=[ret[0].imageExportTaskId])
        i = 0
        for img_task in ret.imageExportTaskSet:
            assert img_task.state == 'completed'
            assert img_task.exportToOsu.diskImageFormat == 'qcow2'
            assert img_task.exportToOsu.osuBucket == self.bucket_names[i]
            assert img_task.imageExport.imageId[i]
            i += 1

    def test_T5359_with_invalid_image_export_task_id(self):
        try:
            self.a1_r1.fcu.DescribeImageExportTasks(imageExportTaskId=['foo'])
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, '', '')
            known_error('TINA-6064', 'DescribeImageExportTasks')

    def test_T5365_with_invalid_type_image_export_task_id(self):
        try:
            self.a1_r1.fcu.DescribeImageExportTasks(imageExportTaskId='foo')
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, '', '')
            known_error('TINA-6064', 'DescribeImageExportTasks')

    @pytest.mark.tag_sec_confidentiality
    def test_T5366_from_another_account(self):
        try:
            self.a2_r1.fcu.DescribeImageExportTasks(imageExportTaskId=[self.image_exp_ids[0]])
            assert False, 'Call from another account should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, '', '')
