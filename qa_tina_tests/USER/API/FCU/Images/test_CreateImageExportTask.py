
"""
    This module describe all test cases for CreateVolume
"""

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state, wait_images_state

NUM_EXPORT_TASK = 5
NUM_IMAGES = NUM_EXPORT_TASK * 5


class Test_CreateImageExportTask(OscTestSuite):
    """
        This class contains all test cases for CreateImageEXportTask
    """

    @classmethod
    def setup_class(cls):
        cls.quotas = {'image_export_limit': NUM_EXPORT_TASK}
        cls.image_ids = []
        cls.inst_info = None
        super(Test_CreateImageExportTask, cls).setup_class()
        try:
            # create 1 instance
            cls.inst_info = create_instances(cls.a1_r1)
            cls.a1_r1.fcu.StopInstances(InstanceId=[cls.inst_info[INSTANCE_ID_LIST][0]], Force=True)
            wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=cls.inst_info[INSTANCE_ID_LIST][0:1], state='stopped')
            for _ in range(NUM_IMAGES):
                ret = cls.a1_r1.fcu.CreateImage(InstanceId=cls.inst_info[INSTANCE_ID_LIST][0], Name=id_generator(prefix='OMI_Test_image_exporttask_'))
                wait_images_state(osc_sdk=cls.a1_r1, image_id_list=[ret.response.imageId], state='available')
                cls.image_ids.append(ret.response.imageId)
            cls.a1_r1.fcu.ModifyImageAttribute(ImageId=cls.image_ids[0], LaunchPermission={'Add': [{'UserId': cls.a2_r1.config.account.account_id}]})
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            for image_id in cls.image_ids:
                cls.a1_r1.fcu.DeregisterImage(ImageId=image_id)
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_CreateImageExportTask, cls).teardown_class()

    def test_T581_without_image_id(self):
        try:
            self.a1_r1.fcu.CreateImageExportTask(ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': 'test'})
            pytest.fail("CreateImageExportTask should not have exceeded")
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: ImageId')

    def test_T741_without_disk_image_format(self):
        try:
            self.a1_r1.fcu.CreateImageExportTask(ImageId=self.image_ids[0], ExportToOsu={'OsuBucket': 'test'})
            pytest.fail("CreateImageExportTask should not have exceeded")
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: DiskImageFormat')

    def test_T742_without_osu_bucket(self):
        try:
            self.a1_r1.fcu.CreateImageExportTask(ImageId=self.image_ids[0], ExportToOsu={'DiskImageFormat': 'qcow2'})
            pytest.fail("CreateImageExportTask should not have exceeded")
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: OsuBucket')

    def test_T582_public_image(self):
        try:
            self.a1_r1.fcu.CreateImageExportTask(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7),
                                                 ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': 'test'})
            pytest.fail("CreateImageExportTask should not have exceeded")
        except OscApiException as error:
            assert_error(error, 400, 'OperationNotPermitted', 'Public or shared images cannot be exported')

    def test_T583_shared_image(self):
        try:
            self.a2_r1.fcu.CreateImageExportTask(ImageId=self.image_ids[0], ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': 'test'})
            pytest.fail("CreateImageExportTask should not have exceeded")
        except OscApiException as error:
            assert_error(error, 400, 'OperationNotPermitted', 'Public or shared images cannot be exported')

    # TODO: add valid tests (need OSU)
    @pytest.mark.region_synchro_osu
    @pytest.mark.region_osu
    def test_T3304_too_many_export_tasks(self):
        for i in range(NUM_IMAGES):
            try:
                self.a1_r1.fcu.CreateImageExportTask(ImageId=self.image_ids[i],
                                                     ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': 'test{}'.format(i)})
            except OscApiException as error:
                assert_error(error, 400, 'PendingImageLimitExceeded',
                             'The limit has exceeded: {}.Limit for Image Exports has been reached.'.format(NUM_EXPORT_TASK))
                return
        assert False, 'Call should not have been successful'
