"""
    This module contains all test cases for describeImageAttribute
"""

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.check_tools import get_snapshot_id_list
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_images
from qa_tina_tools.tools.tina.create_tools import create_image, create_instances_old
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old

UNSUPPORTED_ATT_NAMES = ['kernel', 'ramdisk', 'productCodes', 'sriovNetSupport']
SUPPORTED_ATT_NAMES = ['description', 'launchPermission', 'blockDeviceMapping']
TEST_NAMES = {'description': 1725, 'launchPermission': 1726, 'blockDeviceMapping': 1727,
              'kernel': 1728, 'ramdisk': 1729, 'productCodes': 1730, 'sriovNetSupport': 1731}
DESCRIPTION = id_generator(prefix="description")


class Test_DescribeImageAttribute(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_id = None
        cls.image_name = id_generator(prefix='img_')
        cls.image_id = None
        super(Test_DescribeImageAttribute, cls).setup_class()
        try:
            # create 1 instance
            _, inst_id_list = create_instances_old(cls.a1_r1, state='running')
            cls.inst_id = inst_id_list[0]
            # create image
            ret, cls.image_id = create_image(cls.a1_r1, cls.inst_id, name=cls.image_name, state='available', description=DESCRIPTION)
            cls.img1_snap_id_list = get_snapshot_id_list(ret)
            assert len(cls.img1_snap_id_list) == 1, 'Could not find snapshots created when creating image'
            launch_permissions = {'Add': [{'UserId': str(cls.a2_r1.config.account.account_id)}, {'Group': 'all'}]}
            cls.a1_r1.fcu.ModifyImageAttribute(ImageId=cls.image_id, LaunchPermission=launch_permissions)
        except Exception:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_id:
                delete_instances_old(cls.a1_r1, [cls.inst_id])
            if cls.image_id:
                cleanup_images(cls.a1_r1, image_id_list=[cls.image_id], force=True)
        finally:
            super(Test_DescribeImageAttribute, cls).teardown_class()

    def test_T1725_check_description(self):
        ret = self.a1_r1.fcu.DescribeImageAttribute(Attribute='description', ImageId=self.image_id).response
        assert hasattr(ret, 'description')
        assert hasattr(ret.description, 'value')
        assert ret.description.value == DESCRIPTION

    def test_T1726_check_launchPermission(self):
        ret = self.a1_r1.fcu.DescribeImageAttribute(Attribute='launchPermission', ImageId=self.image_id).response
        assert hasattr(ret, 'launchPermission')
        assert isinstance(ret.launchPermission, list)
        assert len(ret.launchPermission) == 2
        for perm in ret.launchPermission:
            assert hasattr(perm, 'group') or hasattr(perm, 'userId')
            if hasattr(perm, 'group'):
                assert perm.group == 'all'
            if hasattr(perm, 'userId'):
                assert perm.userId == self.a2_r1.config.account.account_id

    def test_T1727_check_blockDeviceMapping(self):
        try:
            self.a1_r1.fcu.DescribeImageAttribute(Attribute='blockDeviceMapping', ImageId=self.image_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', 'This option is not yet implemented: {}'.format('blockDeviceMapping'))

    def test_T1728_check_kernel(self):
        try:
            self.a1_r1.fcu.DescribeImageAttribute(Attribute='kernel', ImageId=self.image_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', 'This option is not yet implemented: {}'.format('kernel'))

    def test_T1729_check_ramdisk(self):
        try:
            self.a1_r1.fcu.DescribeImageAttribute(Attribute='ramdisk', ImageId=self.image_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', 'This option is not yet implemented: {}'.format('ramdisk'))

    def test_T1730_check_productCodes(self):
        self.a1_r1.fcu.DescribeImageAttribute(Attribute='productCodes', ImageId=self.image_id)

    def test_T1731_check_sriovNetSupport(self):
        try:
            self.a1_r1.fcu.DescribeImageAttribute(Attribute='sriovNetSupport', ImageId=self.image_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', 'This option is not yet implemented: {}'.format('sriovNetSupport'))

    def test_T1732_missing_attribute(self):
        try:
            self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: Attribute')

    def test_T1733_unknown_attribute(self):
        try:
            self.a1_r1.fcu.DescribeImageAttribute(Attribute='xxxxxxxxxxx', ImageId=self.image_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', 'This option is not yet implemented: xxxxxxxxxxx')

    def test_T1734_missing_image_id(self):
        try:
            self.a1_r1.fcu.DescribeImageAttribute(Attribute=SUPPORTED_ATT_NAMES[0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: ImageId')

    def test_T1735_incorrect_image_id(self):
        try:
            self.a1_r1.fcu.DescribeImageAttribute(Attribute=SUPPORTED_ATT_NAMES[0], ImageId='xxx-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidAMIID.Malformed', "Invalid id: 'xxx-12345678' (expecting 'ami-...')")

    def test_T1736_unknwon_image_id(self):
        try:
            self.a1_r1.fcu.DescribeImageAttribute(Attribute=SUPPORTED_ATT_NAMES[0], ImageId='ami-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidAMIID.NotFound', "The AMI ID 'ami-12345678' does not exist")
