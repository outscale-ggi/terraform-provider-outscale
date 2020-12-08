from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.check_tools import get_snapshot_id_list
from qa_tina_tools.tools.tina.create_tools import create_instances, create_image
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST

NUM_EXPORT_TASK = 2

class Test_DescribeImageExportTasks(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'image_export_limit': NUM_EXPORT_TASK}
        cls.image_ids = []
        cls.inst_info = None
        cls.image_exp_ids = []
        cls.img_snap_ids = []
        super(Test_DescribeImageExportTasks, cls).setup_class()
        try:
            cls.inst_info = create_instances(cls.a1_r1)
            cls.inst_id = cls.inst_info[INSTANCE_ID_LIST][0]

            for _ in range(NUM_EXPORT_TASK):
                ret, image_id = create_image(cls.a1_r1, cls.inst_id, state='available')
                img_snap_id = get_snapshot_id_list(ret)
                cls.image_ids.append(image_id)
                cls.img_snap_ids.append(img_snap_id)
                image_export_id = cls.a1_r1.fcu.CreateImageExportTask(ImageId=image_id,ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': 'test'}).response.imageExportTask.imageExportTaskId
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
            for img_exp_id in cls.image_exp_ids:
                cls.a1_r1.fcu.CancelExportTask(ExportTaskId=img_exp_id)
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
        ret = self.a1_r1.fcu.DescribeImageExportTasks(imageExportTaskId=self.image_exp_ids[0]).response.imageExportTaskSet
        assert len(ret.imageExportTaskSet) == 1
        assert ret.state == 'completed'
        assert ret.exportToOsu.diskImageFormat == 'qcow2'
        assert ret.exportToOsu.osuBucket == 'test'
        assert ret.imageExport.imageId

    def test_T5358_with_image_export_task_ids(self):
        ret = self.a1_r1.fcu.DescribeImageExportTasks(imageExportTaskId=self.image_exp_ids).response
        assert len(ret.imageExportTaskSet) == 2
        for img_task in ret.imageExportTaskSet:
            assert img_task.state == 'completed'
            assert img_task.exportToOsu.diskImageFormat == 'qcow2'
            assert img_task.exportToOsu.osuBucket == 'test'
            assert img_task.imageExport.imageId

    def test_T5359_with_invalid_image_export_task_id(self):
        try:
            self.a1_r1.fcu.DescribeImageExportTasks(imageExportTaskId='foo')
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, '', '')
            #known_error('', '')
