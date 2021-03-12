import string

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state, wait_images_state, wait_volumes_state


class Test_GetProductTypes(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_GetProductTypes, cls).setup_class()
        cls.name_a1 = id_generator(size=10, chars=string.ascii_letters)
        cls.name_a2 = id_generator(size=10, chars=string.ascii_letters)
        cls.name_a1_a2 = id_generator(size=10, chars=string.ascii_letters)
        cls.name_a2_all = id_generator(size=10, chars=string.ascii_letters)
        cls.instance_info_a1 = None
        cls.instance_info_a2 = None
        cls.instance_info_a1_a2 = None
        cls.instance_info_a2_all = None
        cls.img_id_a1 = None
        cls.img_id_a2 = None
        cls.img_id_a1_a2 = None
        cls.img_id_a2_all = None
        cls.launch_permissions_a1_a2 = {'Add': [{'UserId': str(cls.a1_r1.config.account.account_id)}]}
        cls.launch_permissions_a2_all = {'Add': [{'Group': 'all'}]}

        try:
            cls.instance_info_a1 = create_instances(cls.a1_r1, state=None)
            cls.instance_info_a2 = create_instances(cls.a2_r1, state=None, nb=3)
            wait_instances_state(cls.a1_r1, cls.instance_info_a1[INSTANCE_ID_LIST], state='running')
            wait_instances_state(cls.a2_r1, cls.instance_info_a2[INSTANCE_ID_LIST], state='running')
            cls.img_id_a1 = cls.a1_r1.fcu.CreateImage(InstanceId=cls.instance_info_a1[INSTANCE_ID_LIST][0],
                                                      Name=cls.name_a1).response.imageId
            cls.img_id_a2 = cls.a2_r1.fcu.CreateImage(InstanceId=cls.instance_info_a2[INSTANCE_ID_LIST][0],
                                                      Name=cls.name_a2).response.imageId
            cls.img_id_a1_a2 = cls.a2_r1.fcu.CreateImage(InstanceId=cls.instance_info_a2[INSTANCE_ID_LIST][1],
                                                         Name=cls.name_a1_a2).response.imageId
            cls.img_id_a2_all = cls.a2_r1.fcu.CreateImage(InstanceId=cls.instance_info_a2[INSTANCE_ID_LIST][2],
                                                          Name=cls.name_a2_all).response.imageId

            wait_images_state(osc_sdk=cls.a1_r1, image_id_list=[cls.img_id_a1], state='available')
            wait_images_state(osc_sdk=cls.a2_r1, image_id_list=[cls.img_id_a2], state='available')
            wait_images_state(osc_sdk=cls.a2_r1, image_id_list=[cls.img_id_a1_a2], state='available')
            wait_images_state(osc_sdk=cls.a2_r1, image_id_list=[cls.img_id_a2_all], state='available')
            cls.a2_r1.fcu.ModifyImageAttribute(ImageId=cls.img_id_a1_a2, LaunchPermission=cls.launch_permissions_a1_a2)
            cls.a2_r1.fcu.ModifyImageAttribute(ImageId=cls.img_id_a2_all, LaunchPermission=cls.launch_permissions_a2_all)
            cls.volume_a1 = cls.a1_r1.fcu.CreateVolume(AvailabilityZone=cls.a1_r1.config.region.az_name,
                                                       VolumeType='standard', Size='10')
            cls.volume_a2 = cls.a2_r1.fcu.CreateVolume(AvailabilityZone=cls.a2_r1.config.region.az_name,
                                                       VolumeType='standard', Size='10')
            cls.volume_a1_a2 = cls.a2_r1.fcu.CreateVolume(AvailabilityZone=cls.a2_r1.config.region.az_name,
                                                          VolumeType='standard', Size='10')
            cls.volume_a2_all = cls.a2_r1.fcu.CreateVolume(AvailabilityZone=cls.a2_r1.config.region.az_name,
                                                           VolumeType='standard', Size='10')
            cls.vol_id_a1 = cls.volume_a1.response.volumeId
            cls.vol_id_a2 = cls.volume_a2.response.volumeId
            cls.vol_id_a1_a2 = cls.volume_a1_a2.response.volumeId
            cls.vol_id_a2_all = cls.volume_a2_all.response.volumeId
            wait_volumes_state(cls.a1_r1, [cls.vol_id_a1], state='available', cleanup=False)
            wait_volumes_state(cls.a2_r1, [cls.vol_id_a2], state='available', cleanup=False)
            wait_volumes_state(cls.a2_r1, [cls.vol_id_a1_a2], state='available', cleanup=False)
            wait_volumes_state(cls.a2_r1, [cls.vol_id_a2_all], state='available', cleanup=False)
            cls.snapshot_a1 = cls.a1_r1.fcu.CreateSnapshot(VolumeId=cls.vol_id_a1)
            cls.snap_id_a1 = cls.snapshot_a1.response.snapshotId
            cls.snapshot_a2 = cls.a2_r1.fcu.CreateSnapshot(VolumeId=cls.vol_id_a2)
            cls.snap_id_a2 = cls.snapshot_a2.response.snapshotId
            cls.snapshot_a1_a2 = cls.a2_r1.fcu.CreateSnapshot(VolumeId=cls.vol_id_a1_a2)
            cls.snap_id_a1_a2 = cls.snapshot_a1_a2.response.snapshotId
            cls.snapshot_a2_all = cls.a2_r1.fcu.CreateSnapshot(VolumeId=cls.vol_id_a2_all)
            cls.snap_id_a2_all = cls.snapshot_a2_all.response.snapshotId
            cls.a2_r1.fcu.ModifySnapshotAttribute(SnapshotId=cls.snap_id_a1_a2,
                                                  CreateVolumePermission=cls.launch_permissions_a1_a2)
            cls.a2_r1.fcu.ModifySnapshotAttribute(SnapshotId=cls.snap_id_a2_all,
                                                  CreateVolumePermission=cls.launch_permissions_a2_all)
        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.instance_info_a1:
                delete_instances(cls.a1_r1, cls.instance_info_a1)
            if cls.instance_info_a2:
                delete_instances(cls.a2_r1, cls.instance_info_a2)
            if cls.instance_info_a1_a2:
                delete_instances(cls.a2_r1, cls.instance_info_a1_a2)
            if cls.instance_info_a2_all:
                delete_instances(cls.a2_r1, cls.instance_info_a2_all)
            if cls.img_id_a1:
                cls.a1_r1.fcu.DeregisterImage(ImageId=cls.img_id_a1)
            if cls.img_id_a2:
                cls.a2_r1.fcu.DeregisterImage(ImageId=cls.img_id_a2)
            if cls.img_id_a1_a2:
                cls.a2_r1.fcu.DeregisterImage(ImageId=cls.img_id_a1_a2)
            if cls.img_id_a2_all:
                cls.a2_r1.fcu.DeregisterImage(ImageId=cls.img_id_a2_all)
            if cls.vol_id_a1:
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.vol_id_a1)
            if cls.vol_id_a2:
                cls.a2_r1.fcu.DeleteVolume(VolumeId=cls.vol_id_a2)
            if cls.vol_id_a1_a2:
                cls.a2_r1.fcu.DeleteVolume(VolumeId=cls.vol_id_a1_a2)
            if cls.vol_id_a2_all:
                cls.a2_r1.fcu.DeleteVolume(VolumeId=cls.vol_id_a2_all)
            if cls.snap_id_a1:
                cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=cls.snap_id_a1)
            if cls.snap_id_a2:
                cls.a2_r1.fcu.DeleteSnapshot(SnapshotId=cls.snap_id_a2)
            if cls.snap_id_a1_a2:
                cls.a2_r1.fcu.DeleteSnapshot(SnapshotId=cls.snap_id_a1_a2)
            if cls.snap_id_a2_all:
                cls.a2_r1.fcu.DeleteSnapshot(SnapshotId=cls.snap_id_a2_all)
        finally:
            super(Test_GetProductTypes, cls).teardown_class()

    def test_T4363_without_params(self):
        try:
            self.a1_r1.fcu.GetProductTypes()
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterCombination', 'Either snapshotId or imageId must be set')

    def test_T4364_with_valid_image_id(self):
        ret = self.a1_r1.fcu.GetProductTypes(ImageId=self.img_id_a1)
        assert ret.response.productTypeSet[0]

    def test_T4365_with_valid_snapshot_id(self):
        ret = self.a1_r1.fcu.GetProductTypes(SnapshotId=self.snap_id_a1)

        if ret.response.productTypeSet[0].description is not None:
            known_error('NO TICKET', 'waiting for product decision')

    def test_T4366_with_valid_param_snapshot_id_from_the_image_created(self):
        description = self.a1_r1.fcu.DescribeImages(ImageId=[self.img_id_a1])
        ret = self.a1_r1.fcu.GetProductTypes(SnapshotId=description.response.imagesSet[0].
                                             blockDeviceMapping[0].ebs.snapshotId)
        assert ret.response.productTypeSet[0].description is not None
        assert ret.response.requestId

    def test_T4367_with_all_param_image_id_and_snapshot_id(self):
        try:
            self.a1_r1.fcu.GetProductTypes(ImageId=self.img_id_a1, SnapshotId=self.snap_id_a1)
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterCombination', 'Either snapshotId or imageId must be set')

    def test_T4368_with_image_id_of_an_other_account_without_permission(self):
        try:
            self.a1_r1.fcu.GetProductTypes(ImageId=self.img_id_a2)
        except OscApiException as error:
            assert_error(error, 400, 'InvalidAMIID.NotFound', 'The image ID does not exist: {}'.format(self.img_id_a2))

    def test_T4369_with_image_id_of_an_other_account_with_permission(self):
        ret = self.a1_r1.fcu.GetProductTypes(ImageId=self.img_id_a1_a2)
        assert ret.response.productTypeSet[0]

    def test_T4370_with_image_id_of_an_other_account_with_permission_to_all(self):
        ret = self.a1_r1.fcu.GetProductTypes(ImageId=self.img_id_a2_all)
        assert ret.response.productTypeSet[0]

    def test_T4371_with_a_snapshot_id_from_an_other_account_without_permission(self):
        try:
            self.a1_r1.fcu.GetProductTypes(SnapshotId=self.snap_id_a2)
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshot.NotFound',
                         'The Snapshot ID does not exist: {}, for account: {}'.format(self.snap_id_a2,
                                                                                      self.a1_r1.config.account.account_id))

    def test_T4372_with_snapshot_id_of_an_other_account_with_permission(self):
        ret = self.a1_r1.fcu.GetProductTypes(SnapshotId=self.snap_id_a1_a2)
        assert ret.response.productTypeSet[0]
        assert ret.response.requestId

    def test_T4373_with_snapshot_id_of_an_other_account_with_permission_to_all(self):
        ret = self.a1_r1.fcu.GetProductTypes(SnapshotId=self.snap_id_a2_all)

        assert ret.response.productTypeSet[0]
        assert ret.response.requestId
