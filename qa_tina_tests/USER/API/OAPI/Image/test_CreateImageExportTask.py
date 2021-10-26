
"""
    This module describe all test cases for CreateImageExportTask
"""

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator
from qa_test_tools.config import config_constants
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state, wait_images_state
from specs import check_oapi_error


class Test_CreateImageExportTask(OscTinaTest):
    """
        This class contains all test cases for CreateImageExportTask
    """

    @classmethod
    def setup_class(cls):
        super(Test_CreateImageExportTask, cls).setup_class()
        cls.inst_info = None
        cls.image_id = None
        cls.shared_image_id = None
        try:
            # create 1 instance
            cls.inst_info = create_instances(cls.a1_r1)
            cls.inst_id = cls.inst_info[INSTANCE_ID_LIST][0]

            cls.a1_r1.fcu.StopInstances(InstanceId=[cls.inst_id], Force=True)
            wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=[cls.inst_id], state='stopped')

            ret = cls.a1_r1.fcu.CreateImage(InstanceId=cls.inst_id, Name=id_generator(prefix='OMI_Test_image_exporttask_'))
            cls.image_id = ret.response.imageId

            ret = cls.a1_r1.fcu.CreateImage(InstanceId=cls.inst_id, Name=id_generator(prefix='OMI_Test_image_exporttask_'))
            cls.shared_image_id = ret.response.imageId

            wait_images_state(osc_sdk=cls.a1_r1, image_id_list=[cls.image_id, cls.shared_image_id], state='available')

            cls.a1_r1.fcu.ModifyImageAttribute(ImageId=cls.shared_image_id,
                                               LaunchPermission={'Add': [{'UserId': cls.a2_r1.config.account.account_id}]})
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.image_id:
                cls.a1_r1.fcu.DeregisterImage(ImageId=cls.image_id)
            if cls.shared_image_id:
                cls.a1_r1.fcu.DeregisterImage(ImageId=cls.shared_image_id)
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_CreateImageExportTask, cls).teardown_class()

    def test_T2828_without_image_id(self):
        try:
            self.a1_r1.oapi.CreateImageExportTask(OsuExport={'DiskImageFormat': 'qcow2', 'OsuBucket': 'test'})
            assert False, "CreateImageExportTask should not have succeeded"
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T2829_without_disk_image_format(self):
        try:
            self.a1_r1.oapi.CreateImageExportTask(ImageId=self.image_id, OsuExport={'OsuBucket': 'test'})
            assert False, "CreateImageExportTask should not have succeeded"
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T2830_without_osu_bucket(self):
        try:
            self.a1_r1.oapi.CreateImageExportTask(ImageId=self.image_id, OsuExport={'DiskImageFormat': 'qcow2'})
            assert False, "CreateImageExportTask should not have succeeded"
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T2831_public_image(self):
        try:
            self.a1_r1.oapi.CreateImageExportTask(ImageId=self.a1_r1.config.region.get_info(config_constants.CENTOS_LATEST),
                                                  OsuExport={'DiskImageFormat': 'qcow2', 'OsuBucket': 'test'})
            assert False, "CreateImageExportTask should not have succeeded"
        except OscApiException as error:
            check_oapi_error(error, 8017)

    def test_T2832_shared_image(self):
        try:
            self.a2_r1.oapi.CreateImageExportTask(ImageId=self.shared_image_id, OsuExport={'DiskImageFormat': 'qcow2', 'OsuBucket': 'test'})
            assert False, "CreateImageExportTask should not have succeeded"
        except OscApiException as error:
            check_oapi_error(error, 8017)

    # TODO: add valid tests (need OSU)

    @pytest.mark.region_storageservice
    def test_T2833_with_valid_params(self):
        bucket_name = id_generator(prefix='bn').lower()
        ret = self.a1_r1.oapi.CreateImageExportTask(ImageId=self.image_id,
                                                     OsuExport={'DiskImageFormat': 'qcow2', 'OsuBucket': bucket_name})
        assert ret.response.ImageExportTask
        ret.check_response()
