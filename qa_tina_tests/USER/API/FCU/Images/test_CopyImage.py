from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_images
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old, delete_volumes
from qa_tina_tools.tools.tina.wait_tools import wait_images_state


class Test_CopyImage(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CopyImage, cls).setup_class()

        cls.inst_id = None
        cls.image_name = id_generator(prefix='img_')
        cls.image_id = None
        cls.vol_id = None
        cls.centos = None

        try:
            # get centos public image
            cls.centos = cls.a1_r1.config.region.get_info(constants.CENTOS7)

        except Exception as error:
            cls.logger.exception("An unexpected error happened, while setup")
            cls.teardown_class()
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_id:
                delete_instances_old(cls.a1_r1, [cls.inst_id])

            if cls.vol_id:
                delete_volumes(cls.a1_r1, [cls.vol_id])

            if cls.image_id:
                cleanup_images(cls.a1_r1, image_id_list=[cls.image_id], force=True)

        except Exception as error:
            cls.logger.exception(error)
        finally:
            super(Test_CopyImage, cls).teardown_class()

    def test_T4393_valid_param(self):
        img_id = None
        try:
            ret = self.a1_r1.fcu.CopyImage(SourceImageId=self.centos, SourceRegion=self.a1_r1.config.region.name)
            img_id = ret.response.imageId
            ret = wait_images_state(self.a1_r1, [img_id], state='available')
            assert len(ret.response.imagesSet) == 1
            assert ret.response.imagesSet[0].name.endswith('-copy1')
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)

    def test_T4394_without_source_image_id(self):
        img_id = None
        try:
            img_id = self.a1_r1.fcu.CopyImage(SourceRegion=self.a1_r1.config.region.name).response.imageId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: sourceImageId')
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)

    def test_T4395_without_source_region(self):
        img_id = None
        try:
            img_id = self.a1_r1.fcu.CopyImage(SourceImageId=self.centos).response.imageId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: sourceRegion')
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)

    def test_T4396_with_name(self):
        name = id_generator(prefix='img_')
        img_id = None
        try:
            ret = self.a1_r1.fcu.CopyImage(Name=name, SourceImageId=self.centos, SourceRegion=self.a1_r1.config.region.name)
            img_id = ret.response.imageId
            ret = wait_images_state(self.a1_r1, [img_id], state='available')
            assert len(ret.response.imagesSet) == 1
            assert ret.response.imagesSet[0].name == name
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)

    def test_T4397_incorrect_name(self):
        name = id_generator(prefix='img_', size=300)
        img_id = None
        try:
            img_id = self.a1_r1.fcu.CopyImage(Name=name, SourceImageId=self.centos, SourceRegion=self.a1_r1.config.region.name).response.imageId
            img = self.a1_r1.fcu.DescribeImages(ImageId=[img_id]).response.imagesSet[0]
            assert img.name == name
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)

    def test_T4398_incorrect_source_image_id(self):
        img_id = None
        try:
            img_id = self.a1_r1.fcu.CopyImage(SourceImageId='ami-12345678', SourceRegion=self.a1_r1.config.region.name).response.imageId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidAMIID.NotFound', 'The image ID does not exist: ami-12345678')
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)

    def test_T4399_incorrect_source_region(self):
        img_id = None
        try:
            img_id = self.a1_r1.fcu.CopyImage(SourceImageId=self.centos, SourceRegion='azertyuiop').response.imageId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', 'Inter-region copy is not implemented')
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)

