"""
    This module describe all test cases for describeImages
"""
import time

from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools import constants
from qa_common_tools.misc import id_generator, assert_error
from qa_common_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tina.check_tools import get_snapshot_id_list
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_images
from qa_tina_tools.tools.tina.create_tools import create_volumes, attach_volume, create_image, create_instances_old
from qa_tina_tools.tools.tina.delete_tools import delete_volumes, delete_instances_old
from qa_tina_tools.tools.tina.wait_tools import wait_images_state
import pytest

VOL_SIZE_1 = 11
VOL_SIZE_2 = 123
DESCRIPTION = id_generator(prefix="description")


class Test_DescribeImages(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeImages, cls).setup_class()
        cls.inst_id = None
        cls.vol_id = None
        cls.image_name = id_generator(prefix='img_')
        cls.image1_id = None
        cls.image2_id = None
        try:
            # create 1 instance
            _, inst_id_list = create_instances_old(cls.a1_r1, state='running')
            cls.inst_id = inst_id_list[0]
            # create volume
            _, vol_id_list = create_volumes(cls.a1_r1, size=VOL_SIZE_1)
            cls.vol_id = vol_id_list[0]
            # attach volume
            attach_volume(cls.a1_r1, cls.inst_id, cls.vol_id, '/dev/xvdb')
            # create image
            ret, cls.image1_id = create_image(cls.a1_r1, cls.inst_id, name=cls.image_name, state='available', description=DESCRIPTION)
            cls.img1_snap_id_list = get_snapshot_id_list(ret)
            assert len(cls.img1_snap_id_list) == 2, 'Could not find snapshots created when creating image'
            # add launch permissions to user 2 and user 3
            launch_permissions = {'Add': [{'UserId': str(cls.a2_r1.config.account.account_id)},
                                          {'UserId': str(cls.a3_r1.config.account.account_id)}]}
            cls.a1_r1.fcu.ModifyImageAttribute(ImageId=cls.image1_id, LaunchPermission=launch_permissions)
            # create volume
            _, vol_id_list = create_volumes(cls.a1_r1, size=VOL_SIZE_2, volume_type='io1', iops=100)
            cls.vol_id = vol_id_list[0]
            # attach volume
            attach_volume(cls.a1_r1, cls.inst_id, cls.vol_id, '/dev/xvdc')
            # create image
            ret, cls.image2_id = create_image(cls.a1_r1, cls.inst_id, state='available')
            cls.img2_snap_id_list = get_snapshot_id_list(ret)
            assert len(cls.img2_snap_id_list) == 3, 'Could not find snapshots created when creating image'
            launch_permissions = {'Add': [{'UserId': str(cls.a2_r1.config.account.account_id)}]}
            cls.a1_r1.fcu.ModifyImageAttribute(ImageId=cls.image2_id, LaunchPermission=launch_permissions)
        except Exception as error:
            try:
                cls.teardown_class()
            except:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_id:
                delete_instances_old(cls.a1_r1, [cls.inst_id])
            if cls.vol_id:
                delete_volumes(cls.a1_r1, [cls.vol_id])
            if cls.image1_id:
                cleanup_images(cls.a1_r1, image_id_list=[cls.image1_id], force=True)
            if cls.image2_id:
                cleanup_images(cls.a1_r1, image_id_list=[cls.image2_id], force=True)
        except Exception as error:
            cls.logger.exception(error)
        finally:
            super(Test_DescribeImages, cls).teardown_class()

    def check_invalid_filters(self, filter_name=None, filter_value=None, status_code=200, error_code=None, expected_values=None):
        try:
            desc_filter = {"Name": filter_name, "Value": filter_value}
            ret = self.a2_r1.fcu.DescribeImages(Filter=[desc_filter])
            assert ret.response.imagesSet == expected_values
        except OscApiException as error:
            assert error.status_code == status_code
            assert error.error_code == error_code

    def test_T822_with_no_param(self):
        self.a1_r1.fcu.DescribeImages()

    def test_T823_dry_run(self):
        try:
            self.a1_r1.fcu.DescribeImages(DryRun='true')
            assert False, 'DryRun should have failed'
        except OscApiException as error:
            assert_error(error, 400, 'DryRunOperation', 'Request would have succeeded, but DryRun flag is set.')

    def test_T824_executable_by_user(self):
        # add luanch permissions to user 2 and user 3
        launch_permissions = {'Add': [{'UserId': str(self.a1_r1.config.account.account_id)}]}
        self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image1_id, LaunchPermission=launch_permissions)

        ret = self.a1_r1.fcu.DescribeImages(ExecutableBy=['self'])
        assert len(ret.response.imagesSet) == 1, ret.response.display()

    def test_T825_filter_architecture(self):
        value = "x86_64"
        desc_filter = {"Name": "architecture", "Value": value}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.architecture

    def test_T826_filter_bdm_delete_on_termination(self):
        value = "true"
        desc_filter = {"Name": "block-device-mapping.delete-on-termination", "Value": value}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.blockDeviceMapping[0].ebs.deleteOnTermination

    def test_T827_filter_bdm_device_name(self):
        value = '/dev/sda1'
        desc_filter = {"Name": "block-device-mapping.device-name", "Value": value}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.blockDeviceMapping[0].deviceName

    def test_T828_filter_bdm_snapshot_id(self):
        desc_filter = {"Name": "block-device-mapping.snapshot-id", "Value": self.img1_snap_id_list[0]}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        assert ret.response.imagesSet and len(ret.response.imagesSet) == 1 and ret.response.imagesSet[0].imageId == self.image1_id

    def test_T829_filter_bdm_volume_size(self):
        desc_filter = {"Name": "block-device-mapping.volume-size", "Value": str(VOL_SIZE_2)}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        try:
            assert ret.response.imagesSet and len(ret.response.imagesSet) == 1 and ret.response.imagesSet[0].imageId == self.image2_id
            pytest.fail('Remove known error code')
        except AssertionError:
            known_error('TINA-5352', 'Could not filter using block-device-mapping.volume-size')

    def test_T830_filter_bdm_volume_type(self):
        desc_filter = {"Name": "block-device-mapping.volume-type", "Value": "io1"}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        assert ret.response.imagesSet and len(ret.response.imagesSet) == 1 and ret.response.imagesSet[0].imageId == self.image2_id

    def test_T831_filter_description(self):
        value = DESCRIPTION
        desc_filter = {"Name": "description", "Value": DESCRIPTION}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.description

    def test_T832_filter_hypervisor(self):
        value = 'xen'
        desc_filter = {"Name": "hypervisor", "Value": value}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.hypervisor

    def test_T833_filter_image_id(self):
        value = self.a1_r1._config.region._conf[constants.CENTOS7]
        desc_filter = {"Name": "image-id", "Value": value}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.imageId

    def test_T834_filter_image_type(self):
        value = 'machine'
        desc_filter = {"Name": "image-type", "Value": value}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.imageType

    def test_T835_filter_is_public(self):
        value = 'true'
        desc_filter = {"Name": "is-public", "Value": value}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.isPublic

    # def test_T836_filter_kernel_id(self): --> filter not supported

    # def test_T837_filter_manifest_location(self):

    def test_T838_filter_name(self):
        value = self.image_name
        desc_filter = {"Name": "name", "Value": value}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.name

    def test_T839_filter_owner_alias(self):
        desc_filter = {"Name": "owner-alias", "Value": "Outscale"}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        assert ret.response.imagesSet and len(ret.response.imagesSet) > 0
        for img in ret.response.imagesSet:
            assert img.imageOwnerAlias == 'Outscale'

    def test_T840_filter_owner_id(self):
        value = self.a1_r1.config.account.account_id
        desc_filter = {"Name": "owner-id", "Value": value}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.imageOwnerId

    def test_T841_filter_platform(self):
        value = "windows"
        desc_filter = {"Name": "platform", "Value": value}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.platform

    # def test_T842_filter_product_code(self): --> filter not supported

    # def test_T843_filter_ram_disk(self): --> filter not supported

    def test_T844_filter_root_device_name(self):
        value = '/dev/sda1'
        desc_filter = {"Name": "root-device-name", "Value": value}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.rootDeviceName

    def test_T845_filter_root_device_type(self):
        value = "ebs"
        desc_filter = {"Name": "root-device-type", "Value": value}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.rootDeviceType

    def test_T846_filter_state(self):
        value = "available"
        desc_filter = {"Name": "state", "Value": value}
        wait_images_state(osc_sdk=self.a1_r1, image_id_list=[self.image1_id], state=value)
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.imageState

    def test_T1387_filter_root_device_virtualization_type(self):
        value = "hvm"
        desc_filter = {"Name": "virtualization-type", "Value": value}
        ret = self.a1_r1.fcu.DescribeImages(Filter=[desc_filter])
        for image in ret.response.imagesSet:
            assert value == image.virtualizationType

    def test_T1369_valid_image_id_my_image(self):
        ret = self.a1_r1.fcu.DescribeImages(ImageId=[self.image1_id])
        assert len(ret.response.imagesSet) == 1, ret.response.display()
        assert ret.response.imagesSet[0].imageId == self.image1_id, ret.response.display()

    def test_T1370_valid_image_id_public_image(self):
        ret = self.a1_r1.fcu.DescribeImages(ImageId=[self.a1_r1._config.region._conf[constants.CENTOS7]])
        assert len(ret.response.imagesSet) == 1, ret.response.display()
        assert ret.response.imagesSet[0].imageId == self.a1_r1._config.region._conf[constants.CENTOS7], ret.response.display()

    def test_T1371_valid_image_id_shared_image(self):
        ret = self.a2_r1.fcu.DescribeImages(ImageId=[self.image1_id])
        assert len(ret.response.imagesSet) == 1, ret.response.display()
        assert ret.response.imagesSet[0].imageId == self.image1_id, ret.response.display()
        assert ret.response.imagesSet[0].imageOwnerId == self.a1_r1.config.account.account_id

    def test_T1372_invalid_image_id_foo(self):
        try:
            self.a1_r1.fcu.DescribeImages(ImageId='foo')
            assert False, 'Call should have failed'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'InvalidAMIID.Malformed'

    def test_T1373_invalid_image_id_not_exist(self):
        try:
            self.a1_r1.fcu.DescribeImages(ImageId='ami-1234578')
            assert False, 'Call should have failed'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'InvalidAMIID.NotFound'

    def test_T1374_invalid_image_id_partially_exist(self):
        # i-yyyxxxxxxxx (i-xxxxxxxx exist)
        try:
            image_id = "{}yyy{}".format(self.image1_id[:4], self.image1_id[-8:])
            self.a1_r1.fcu.DescribeImages(ImageId=image_id)
            assert False, 'Call should have failed'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'InvalidAMIID.Malformed'

    def test_T1375_invalid_image_if_exist_not_shared(self):
        try:
            self.a3_r1.fcu.DescribeImages(ImageId=self.image2_id)
            assert False, 'Call should have failed'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'InvalidAMIID.NotFound'

    def test_T1376_valid_exectutable_my_own_image(self):
        # Scopes the images by users with explicit launch permissions.
        # Specify an AWS account ID, self (the sender of the request), or all (public AMIs).
        ret = self.a2_r1.fcu.DescribeImages(ExecutableBy=[self.a2_r1.config.account.account_id])
        assert len(ret.response.imagesSet) == 2, ret.response.display()
        for image in ret.response.imagesSet:
            assert self.a1_r1.config.account.account_id == image.imageOwnerId

    def test_T1377_valid_executable_another_account_shared_ami(self):
        ret = self.a1_r1.fcu.DescribeImages(ExecutableBy=[self.a2_r1.config.account.account_id])
        assert len(ret.response.imagesSet) == 2, ret.response.display()
    # TDOD to be verified:

    def test_T1378_valid_executable_common_ami(self):
        ret = self.a3_r1.fcu.DescribeImages(ExecutableBy=[self.a2_r1.config.account.account_id])
        assert ret.response.imagesSet is None or len(ret.response.imagesSet) == 0, ret.response.display()

    def test_T1379_valid_executable_all(self):
        ret = self.a3_r1.fcu.DescribeImages(ExecutableBy=['all'])
        for image in ret.response.imagesSet:
            assert 'true' == image.isPublic

    def test_T1527_valid_executable_self(self):
        ret = self.a3_r1.fcu.DescribeImages(ExecutableBy=['self'])
        assert len(ret.response.imagesSet) == 1, ret.response.display()
        assert ret.response.imagesSet[0].imageId == self.image1_id

    def test_T1380_invalid_exectutable_foo(self):
        # https://jira.outscale.internal/browse/TINA-3872
        try:
            self.a1_r1.fcu.DescribeImages(ExecutableBy=['foo'])
            known_error('TINA-3872', 'Incorrect account id should trigger error')
            assert False, 'Call should have failed'
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert error.status_code == 400
            assert error.error_code == 'InvalidUserID.Malformed'

    def test_T1381_invalid_executable_non_existing(self):
        # https://jira.outscale.internal/browse/TINA-3872
        try:
            self.a1_r1.fcu.DescribeImages(ExecutableBy=['000000000000'])
            known_error('TINA-3872', 'Incorrect account id should trigger error')
            assert False, 'Call should have failed'
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert error.status_code == 400
            assert error.error_code == 'InvalidUserID.Malformed'

    def test_T1382_valid_owner_id_my_own_AMI(self):
        ret = self.a1_r1.fcu.DescribeImages(Owner=[self.a1_r1.config.account.account_id])
        assert len(ret.response.imagesSet) == 2, ret.response.display()
        assert self.a1_r1.config.account.account_id in (image.imageOwnerId for image in ret.response.imagesSet)

    def test_T1391_with_valid_owner_id_self(self):
        ret = self.a1_r1.fcu.DescribeImages(Owner=['self'])
        assert len(ret.response.imagesSet) == 2, ret.response.display()
        assert self.a1_r1.config.account.account_id in (image.imageOwnerId for image in ret.response.imagesSet)

    def test_T1383_valid_owner_id_another_Account_shared_AMI(self):
        ret = self.a2_r1.fcu.DescribeImages(Owner=[self.a1_r1.config.account.account_id])
        assert len(ret.response.imagesSet) == 2, ret.response.display()
        assert self.a1_r1.config.account.account_id in (image.imageOwnerId for image in ret.response.imagesSet)

    def test_T1384_invalid_owner_id_foo(self):
        # https://jira.outscale.internal/browse/TINA-3872
        """InvalidUserID.Malformed
              The specified  user or owner is not valid.If  you   are  performing  a DescribeImages
              request, you  must  specify  a valid value
              for the owner or executableBy parameters, such as an AWS account ID.
              If you are performing a DescribeSnapshots request, you must specify a valid
               value for the owner or restorableBy parameters."""
        # https://jira.outscale.internal/browse/TINA-3872
        try:
            self.a2_r1.fcu.DescribeImages(Owner=['foo'])
            known_error('TINA-3872', 'Incorrect account id should trigger error')
            assert False, 'Call should have failed'
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert error.status_code == 400
            assert error.error_code == 'InvalidUserID.Malformed'

    def test_T1385_invalid_owner_id_non_existing(self):
        # https://jira.outscale.internal/browse/TINA-3872
        try:
            self.a2_r1.fcu.DescribeImages(Owner=['000000000000'])
            known_error('TINA-3872', 'Incorrect account id should trigger error')
            assert False, 'Call should have failed'
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert error.status_code == 400
            assert error.error_code == 'InvalidUserID.Malformed'

    def test_T1386_invalid_owner_id_existing_user_no_AMI(self):
        ret = self.a2_r1.fcu.DescribeImages(Owner=[self.a2_r1.config.account.account_id])
        assert ret.response.imagesSet is None

    def test_T1343_invalid_filter_architecture(self):
        self.check_invalid_filters(filter_name="architecture", filter_value="foo")

    def test_T1344_invalid_filter_block_device_delete_ont_termination(self):
        self.check_invalid_filters(filter_name="block-device-mapping.delete-on-termination", filter_value="foo")

    def test_T1345_invalid_filter_block_device_mapping_device_name(self):
        self.check_invalid_filters(filter_name="block-device-mapping.device-name", filter_value="foo")

    def test_T1346_invalid_filter_block_device_mapping_snapshot_id(self):
        self.check_invalid_filters(filter_name="block-device-mapping.snapshot-id", filter_value="foo")

    def test_T1347_invalid_filter_block_device_mapping_volume_size(self):
        self.check_invalid_filters(filter_name="block-device-mapping.volume-size", filter_value="foo")

    def test_T1348_invalid_filter_block_device_mapping_volume_type(self):
        self.check_invalid_filters(filter_name="block-device-mapping.volume-type", filter_value="foo")

    def test_T1349_invalid_filter_description(self):
        self.check_invalid_filters(filter_name="description", filter_value="foo")

    def test_T1350_invalid_filter_hypervisor(self):
        self.check_invalid_filters(filter_name="hypervisor", filter_value="foo")

    def test_T1351_invalid_filter_image_id(self):
        self.check_invalid_filters(filter_name="image-id", filter_value="foo")

    def test_T1352_invalid_filter_image_type(self):
        self.check_invalid_filters(filter_name="image-type", filter_value="foo")

    def test_T1353_invalid_filter_is_public(self):
        self.check_invalid_filters(filter_name="is-public", filter_value="foo")

    def test_T1354_invalid_filter_kernel_id(self):
        self.check_invalid_filters(filter_name="kernel-id", filter_value="foo")

    def test_T1355_invalid_filter_manifest_location(self):
        self.check_invalid_filters(filter_name="manisfest-location", filter_value="foo")

    def test_T1356_invalid_filter_name(self):
        self.check_invalid_filters(filter_name="name", filter_value="foo")

    def test_T1357_invalid_filter_owner_alias(self):
        self.check_invalid_filters(filter_name="owner-alias", filter_value="foo")

    def test_T1358_invalid_filter_owner_id(self):
        self.check_invalid_filters(filter_name="owner-id", filter_value="foo")

    def test_T1359_invalid_filter_platform(self):
        self.check_invalid_filters(filter_name="platform", filter_value="foo")

    def test_T1360_invalid_filter_product_code(self):
        self.check_invalid_filters(filter_name="product-code", filter_value="foo")

    def test_T1361_invalid_filter_ramdisk_id(self):
        self.check_invalid_filters(filter_name="ramdisk-id", filter_value="foo")

    def test_T1362_invalid_filter_root_device_name(self):
        self.check_invalid_filters(filter_name="root-device-name", filter_value="foo")

    def test_T1363_invalid_filter_root_device_type(self):
        self.check_invalid_filters(filter_name="root-device-type", filter_value="foo")

    def test_T1364_invalid_filter_state(self):
        self.check_invalid_filters(filter_name="state", filter_value="foo")

    def test_T1365_invalid_filter_tag_key_value(self):
        self.check_invalid_filters(filter_name="tag:test", filter_value="foo")

    def test_T1366_invalid_filter_tag_key(self):
        self.check_invalid_filters(filter_name="tag:key", filter_value="foo")

    def test_T1367_invalid_filter_tag_value(self):
        self.check_invalid_filters(filter_name="tag-value", filter_value="foo")

    def test_T1368_invalid_filter_virtualization_type(self):
        self.check_invalid_filters(filter_name="virtualization-type", filter_value="foo")
