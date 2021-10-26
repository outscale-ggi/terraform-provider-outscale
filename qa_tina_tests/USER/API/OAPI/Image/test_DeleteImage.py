import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import assert_dry_run
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.wait_tools import wait_images_state
from specs import check_oapi_error


class Test_DeleteImage(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteImage, cls).setup_class()
        cls.image_id = None
        try:
            image_id = cls.a1_r1.config.region.get_info(constants.CENTOS_LATEST)
            cls.image_id = cls.a1_r1.oapi.CreateImage(
                SourceImageId=image_id, SourceRegionName=cls.a1_r1.config.region.name).response.Image.ImageId
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.image_id:
                cls.a1_r1.oapi.DeleteImage(ImageId=cls.image_id)
        finally:
            super(Test_DeleteImage, cls).teardown_class()

    def test_T2215_valid_params(self):
        img_id = None
        try:
            img_id = self.a1_r1.oapi.CreateImage(SourceImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                                 SourceRegionName=self.a1_r1.config.region.name).response.Image.ImageId
            wait_images_state(self.a1_r1, [img_id], state='available')
            self.a1_r1.oapi.DeleteImage(ImageId=img_id)
            img_id = None
        finally:
            if img_id:
                self.a1_r1.oapi.DeleteImage(ImageId=img_id)

    def test_T2216_valid_params_dry_run(self):
        img_id = None
        try:
            img_id = self.a1_r1.oapi.CreateImage(SourceImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                                 SourceRegionName=self.a1_r1.config.region.name).response.Image.ImageId
            wait_images_state(self.a1_r1, [img_id], state='available')
            ret = self.a1_r1.oapi.DeleteImage(ImageId=img_id, DryRun=True)
            assert_dry_run(ret)
        finally:
            if img_id:
                self.a1_r1.oapi.DeleteImage(ImageId=img_id)

    def test_T2301_empty_param(self):
        try:
            self.a1_r1.oapi.DeleteImage()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T2302_invalid_image_id(self):
        try:
            self.a1_r1.oapi.DeleteImage(ImageId='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='tata', prefixes='aki-, ami-, ari-')

    def test_T2303_unknown_image_id(self):
        try:
            self.a1_r1.oapi.DeleteImage(ImageId='ami-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5023, id='ami-12345678')

    @pytest.mark.tag_sec_confidentiality
    def test_T3544_with_other_user(self):
        img_id = None
        try:
            img_id = self.a1_r1.oapi.CreateImage(SourceImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                                 SourceRegionName=self.a1_r1.config.region.name).response.Image.ImageId
            wait_images_state(self.a1_r1, [img_id], state='available')
            self.a2_r1.oapi.DeleteImage(ImageId=img_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5)
        finally:
            if img_id:
                self.a1_r1.oapi.DeleteImage(ImageId=img_id)
