# -*- coding:utf-8 -*-
import pytest
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.constants import CENTOS7
from qa_common_tools.misc import id_generator, assert_oapi_error, assert_dry_run
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_volumes
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state, wait_images_state
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST


class Test_CreateImage(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateImage, cls).setup_class()
        cls.inst_info = None
        cls.image_id = None
        cls.volume_ids = None
        cls.snap_id1 = None
        try:
            _, cls.volume_ids = create_volumes(cls.a1_r1, size=2, count=2)
            wait_volumes_state(cls.a1_r1, cls.volume_ids, state='available')
            cls.snap1_id = cls.a1_r1.oapi.CreateSnapshot(VolumeId=cls.volume_ids[0]).response.Snapshot.SnapshotId
            cls.inst_info = create_instances(cls.a1_r1, nb=2)
            cls.inst_id = cls.inst_info[INSTANCE_ID_LIST][0]
            cls.inst_id2 = cls.inst_info[INSTANCE_ID_LIST][1]
            cls.a1_r1.oapi.LinkVolume(VolumeId=cls.volume_ids[1], VmId=cls.inst_id2, DeviceName='/dev/xvdb')
            wait_volumes_state(cls.a1_r1, cls.volume_ids[1:2], state='in-use')
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
            if cls.snap1_id:
                cls.a1_r1.oapi.DeleteSnapshot(SnapshotId=cls.snap1_id)
            if cls.volume_ids:
                delete_volumes(cls.a1_r1, cls.volume_ids)
        finally:
            super(Test_CreateImage, cls).teardown_class()

    def setup_method(self, method):
        super(Test_CreateImage, self).setup_method(method)
        self.ami_name = id_generator(prefix='imgname_')
        self.image_id = None

    def teardown_method(self, method):
        try:
            if self.image_id:
                wait_images_state(self.a1_r1, [self.image_id], state='available')
                self.a1_r1.oapi.DeleteImage(ImageId=self.image_id)
        finally:
            super(Test_CreateImage, self).teardown_method(method)

    def test_T2294_empty_param(self):
        try:
            self.a1_r1.oapi.CreateImage()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    def test_T2318_only_name(self):
        try:
            self.a1_r1.oapi.CreateImage(ImageName=self.ami_name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    def test_T2677_invalid_parameters_combinations(self):
        try:
            self.a1_r1.oapi.CreateImage(VmId=self.inst_id, ImageName=self.ami_name, SourceImageId=self.a1_r1.config.region.get_info(CENTOS7))
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)

        try:
            self.a1_r1.oapi.CreateImage(VmId=self.inst_id, ImageName=self.ami_name, SourceRegionName=self.a1_r1.config.region.name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)

        try:
            self.a1_r1.oapi.CreateImage(VmId=self.inst_id, ImageName=self.ami_name,
                                        BlockDeviceMappings=[{'DeviceName': '/dev/sda1', 'Bsu': {'SnapshotId': self.snap1_id}}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)

        try:
            self.a1_r1.oapi.CreateImage(VmId=self.inst_id, ImageName=self.ami_name, Architecture='x86')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)

        try:
            self.a1_r1.oapi.CreateImage(VmId=self.inst_id, ImageName=self.ami_name, RootDeviceName='/dev/sda1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)

        try:
            self.a1_r1.oapi.CreateImage(SourceImageId=self.a1_r1.config.region.get_info(CENTOS7),
                                        ImageName=self.ami_name, RootDeviceName='/dev/sda1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)

        try:
            self.a1_r1.oapi.CreateImage(VmId=self.inst_id, FileLocation='%s/NewOmi' % self.a1_r1.config.account.account_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)

        try:
            self.a1_r1.oapi.CreateImage(NoReboot=True, FileLocation='%s/NewOmi' % self.a1_r1.config.account.account_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)

        try:
            self.a1_r1.oapi.CreateImage(Architecture='x86', FileLocation='%s/NewOmi' % self.a1_r1.config.account.account_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)

        try:
            self.a1_r1.oapi.CreateImage(RootDeviceName='/dev/sda1', FileLocation='%s/NewOmi' % self.a1_r1.config.account.account_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)

    def test_T2213_from_vm_valid_params(self):
        self.image_id = self.a1_r1.oapi.CreateImage(VmId=self.inst_id, ImageName=self.ami_name).response.Image.ImageId
        assert self.image_id.startswith('ami-')

    def test_T2214_from_vm_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.CreateImage(VmId=self.inst_id, ImageName=self.ami_name, DryRun=True)
        assert_dry_run(ret)

    def test_T2295_from_vm_invalid_vm_id(self):
        try:
            self.a1_r1.oapi.CreateImage(VmId='tata', ImageName='ami1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104', None)

    def test_T2296_from_vm_unknown_vm_id(self):
        try:
            self.a1_r1.oapi.CreateImage(VmId='i-12345678', ImageName='ami1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063', None)

    def test_T2297_from_vm_no_name(self):
        try:
            self.a1_r1.oapi.CreateImage(VmId='i-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)

    def test_T2298_from_vm_valid_case(self):
        ret = self.a1_r1.oapi.CreateImage(VmId=self.inst_id, ImageName=self.ami_name).response.Image
        self.image_id = ret.ImageId
        assert self.image_id.startswith('ami-')
        assert ret.AccountId == self.a1_r1.config.account.account_id
        assert ret.Architecture == 'x86_64'
        assert len(ret.BlockDeviceMappings) == 1
        assert ret.BlockDeviceMappings[0].DeviceName == '/dev/sda1'
        assert ret.BlockDeviceMappings[0].Bsu.DeleteOnVmDeletion
        assert ret.BlockDeviceMappings[0].Bsu.SnapshotId.startswith('snap-')
        assert hasattr(ret.BlockDeviceMappings[0].Bsu, 'VolumeSize')
        assert ret.BlockDeviceMappings[0].Bsu.VolumeType == 'standard'
        assert ret.Description == ''
        assert ret.ImageName == self.ami_name
        assert ret.FileLocation is not ''
        assert not ret.PermissionsToLaunch.GlobalPermission
        assert ret.PermissionsToLaunch.AccountIds == []
        assert ret.ProductCodes is not None
        assert ret.RootDeviceName == '/dev/sda1'
        assert ret.RootDeviceType == 'bsu'
        assert ret.State == 'available' or 'pending'
        assert ret.StateComment is not None
        assert ret.Tags == []
        wait_images_state(self.a1_r1, [self.image_id], state='available')

    def test_T2299_from_vm_valid_case_with_description(self):
        ret = self.a1_r1.oapi.CreateImage(VmId=self.inst_id, ImageName=self.ami_name,
                                          Description='Hello I am the first AMI created in this test').response.Image
        self.image_id = ret.ImageId
        assert self.image_id.startswith('ami-')
        assert ret.AccountId == self.a1_r1.config.account.account_id
        assert ret.Architecture == 'x86_64'
        assert len(ret.BlockDeviceMappings) == 1
        assert ret.BlockDeviceMappings[0].DeviceName == '/dev/sda1'
        assert ret.BlockDeviceMappings[0].Bsu.DeleteOnVmDeletion
        assert ret.BlockDeviceMappings[0].Bsu.SnapshotId.startswith('snap-')
        assert hasattr(ret.BlockDeviceMappings[0].Bsu, 'VolumeSize')
        assert ret.BlockDeviceMappings[0].Bsu.VolumeType == 'standard'
        assert ret.Description == 'Hello I am the first AMI created in this test'
        assert ret.ImageName == self.ami_name
        assert ret.FileLocation is not ''
        assert not ret.PermissionsToLaunch.GlobalPermission
        assert ret.PermissionsToLaunch.AccountIds == []
        assert ret.ProductCodes is not None
        assert ret.RootDeviceName == '/dev/sda1'
        assert ret.RootDeviceType == 'bsu'
        assert ret.State == 'available' or 'pending'
        assert ret.StateComment is not None
        assert ret.Tags == []
        wait_images_state(self.a1_r1, [self.image_id], state='available')

    def test_T2300_from_vm_valid_case_with_description_no_reboot_false(self):
        ret = self.a1_r1.oapi.CreateImage(VmId=self.inst_id, ImageName=self.ami_name,
                                          Description='Hello I am the second AMI created in this test :D',
                                          NoReboot=False).response.Image
        self.image_id = ret.ImageId
        assert self.image_id.startswith('ami-')
        assert ret.AccountId == self.a1_r1.config.account.account_id
        assert ret.Architecture == 'x86_64'
        assert len(ret.BlockDeviceMappings) == 1
        assert ret.BlockDeviceMappings[0].DeviceName == '/dev/sda1'
        assert ret.BlockDeviceMappings[0].Bsu.DeleteOnVmDeletion
        assert ret.BlockDeviceMappings[0].Bsu.SnapshotId.startswith('snap-')
        assert hasattr(ret.BlockDeviceMappings[0].Bsu, 'VolumeSize')
        assert ret.BlockDeviceMappings[0].Bsu.VolumeType == 'standard'
        assert ret.Description == 'Hello I am the second AMI created in this test :D'
        assert ret.ImageName == self.ami_name
        assert ret.FileLocation is not ''
        assert not ret.PermissionsToLaunch.GlobalPermission
        assert ret.PermissionsToLaunch.AccountIds == []
        assert ret.ProductCodes is not None
        assert ret.RootDeviceName == '/dev/sda1'
        assert ret.RootDeviceType == 'bsu'
        assert ret.State == 'available' or 'pending'
        assert ret.StateComment is not None
        assert ret.Tags == []
        wait_images_state(self.a1_r1, [self.image_id], state='available')

    def test_T2211_from_copy_valid_params(self):
        self.image_id = self.a1_r1.oapi.CreateImage(SourceImageId=self.a1_r1.config.region.get_info(CENTOS7),
                                                    SourceRegionName=self.a1_r1.config.region.name
                                                    ).response.Image.ImageId
        assert self.image_id.startswith('ami-')

    def test_T2212_from_copy_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.CreateImage(SourceImageId=self.a1_r1.config.region.get_info(CENTOS7),
                                          SourceRegionName=self.a1_r1.config.region.name,
                                          DryRun=True)
        assert_dry_run(ret)

    def test_T2290_from_copy_invalid_image_id(self):
        try:
            self.a1_r1.oapi.CreateImage(SourceImageId='tata', SourceRegionName=self.a1_r1.config.region.name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104', None)

    def test_T2291_from_copy_unknown_image_id(self):
        try:
            self.a1_r1.oapi.CreateImage(SourceImageId='ami-12345678', SourceRegionName=self.a1_r1.config.region.name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5023', None)

    def test_T2292_from_copy_unknown_invalid_region(self):
        try:
            self.a1_r1.oapi.CreateImage(SourceImageId=self.a1_r1.config.region.get_info(CENTOS7),
                                        SourceRegionName='alpha')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'OperationNotSupported', '8019', None)

    def test_T2293_from_copy_valid_case(self):
        source_img_id = self.a1_r1.config.region.get_info(CENTOS7)
        ret = self.a1_r1.oapi.CreateImage(SourceImageId=source_img_id,
                                          SourceRegionName=self.a1_r1.config.region.name).response.Image
        self.image_id = ret.ImageId
        # wait_images_state(self.a1_r1, [img_id], state='available')
        assert self.image_id.startswith('ami-')
        assert source_img_id != self.image_id
        assert ret.AccountId == self.a1_r1.config.account.account_id
        assert ret.Architecture == 'x86_64'
        assert len(ret.BlockDeviceMappings) == 1
        assert ret.BlockDeviceMappings[0].DeviceName == '/dev/sda1'
        assert ret.BlockDeviceMappings[0].Bsu.DeleteOnVmDeletion
        assert ret.BlockDeviceMappings[0].Bsu.SnapshotId.startswith('snap-')
        assert hasattr(ret.BlockDeviceMappings[0].Bsu, 'VolumeSize')
        assert ret.BlockDeviceMappings[0].Bsu.VolumeType == 'standard'
        assert hasattr(ret, 'Description')  # description in copy case is different between dk/in/dv
        # assert ret.ImageName.startswith('CentOS 7 (20182201)-copy')
        assert ret.FileLocation is not ''
        assert ret.PermissionsToLaunch.GlobalPermission
        assert ret.PermissionsToLaunch.AccountIds == []
        assert ret.ProductCodes is not None
        assert ret.RootDeviceName == '/dev/sda1'
        assert ret.RootDeviceType == 'bsu'
        assert ret.State == 'available' or 'pending'
        assert ret.StateComment is not None
        assert ret.Tags == []

    @pytest.mark.region_osu
    def test_T2319_from_manifest_valid_osu_location(self):
        ret = self.a1_r1.oapi.CreateImage(ImageName=self.ami_name,
                                          FileLocation='%s/NewOmi' % self.a1_r1.config.account.account_id).response.Image
        self.image_id = ret.ImageId
        assert self.image_id.startswith('ami-')
        assert ret.FileLocation is not ''

    def test_T2320_from_snap_valid_bdm_simplest_case(self):
        ret = self.a1_r1.oapi.CreateImage(ImageName=self.ami_name, RootDeviceName='/dev/sda1',
                                          BlockDeviceMappings=[{'DeviceName': '/dev/sda1', 'Bsu': {'SnapshotId': self.snap1_id}}]).response.Image
        self.image_id = ret.ImageId
        assert self.image_id.startswith('ami-')
        assert ret.AccountId == self.a1_r1.config.account.account_id
        assert ret.Architecture == 'i386'
        assert ret.Description == ''
        assert len(ret.BlockDeviceMappings) == 1
        assert ret.BlockDeviceMappings[0].DeviceName == '/dev/sda1'
        assert ret.BlockDeviceMappings[0].Bsu.DeleteOnVmDeletion
        assert ret.BlockDeviceMappings[0].Bsu.SnapshotId == self.snap1_id
        assert ret.ImageName == self.ami_name
        assert ret.FileLocation is not ''
        assert not ret.PermissionsToLaunch.GlobalPermission
        assert ret.PermissionsToLaunch.AccountIds == []
        assert ret.ProductCodes is not None
        assert ret.RootDeviceName == '/dev/sda1'
        assert ret.RootDeviceType == 'bsu'
        assert ret.State == 'available'
        assert ret.StateComment is not None
        assert ret.Tags == []

    # @pytest.mark.skip('disabled - Needs to be rewritten')
    # def test_T2321_from_snap_valid_bdm_delete_on_vm_deletion_false(self):
    #    ret = self.a1_r1.oapi.CreateImage(ImageName=self.ami_name, RootDeviceName='/dev/sda1', BlockDeviceMappings=[
    #        {'DeviceName': '/dev/sda1', 'Bsu': {'SnapshotId': self.snap1_id, 'DeleteOnVmDeletion': False}
    #         }]).response.Image
    #    self.image_id = ret.ImageId
    #    assert self.image_id.startswith('ami-')
    #    assert len(ret.BlockDeviceMappings) == 1
    #    assert ret.BlockDeviceMappings[0].DeviceName == '/dev/sda1'
    #    assert not ret.BlockDeviceMappings[0].Bsu.DeleteOnVmDeletion
    #    assert ret.BlockDeviceMappings[0].Bsu.SnapshotId == self.snap1_id

    def test_T2322_from_snap_valid_bdm_volume_type(self):
        ret = self.a1_r1.oapi.CreateImage(ImageName=self.ami_name, RootDeviceName='/dev/sda1', BlockDeviceMappings=[
            {'DeviceName': '/dev/sda1', 'Bsu': {'SnapshotId': self.snap1_id, 'VolumeType': 'standard'}}]).response.Image
        self.image_id = ret.ImageId
        assert self.image_id.startswith('ami-')
        assert len(ret.BlockDeviceMappings) == 1
        assert len(ret.BlockDeviceMappings) == 1
        assert ret.BlockDeviceMappings[0].DeviceName == '/dev/sda1'
        assert ret.BlockDeviceMappings[0].Bsu.DeleteOnVmDeletion
        assert ret.BlockDeviceMappings[0].Bsu.SnapshotId == self.snap1_id
        assert ret.BlockDeviceMappings[0].Bsu.VolumeType == 'standard'
        assert ret.FileLocation is not ''

    def test_T2323_from_snap_valid_bdm_volume_size(self):
        ret = self.a1_r1.oapi.CreateImage(ImageName=self.ami_name, RootDeviceName='/dev/sda1', BlockDeviceMappings=[
            {'DeviceName': '/dev/sda1', 'Bsu': {'SnapshotId': self.snap1_id, 'VolumeSize': 2}}]).response.Image
        self.image_id = ret.ImageId
        assert self.image_id.startswith('ami-')
        assert len(ret.BlockDeviceMappings) == 1
        assert ret.BlockDeviceMappings[0].DeviceName == '/dev/sda1'
        assert ret.BlockDeviceMappings[0].Bsu.DeleteOnVmDeletion
        assert ret.BlockDeviceMappings[0].Bsu.SnapshotId.startswith('snap-')
        assert ret.BlockDeviceMappings[0].Bsu.VolumeSize == 2
        assert ret.FileLocation is not ''

    def test_T2324_from_snap_valid_bdm_iops(self):
        ret = self.a1_r1.oapi.CreateImage(ImageName=self.ami_name, RootDeviceName='/dev/sda1', BlockDeviceMappings=[
            {'DeviceName': '/dev/sda1',
             'Bsu': {'SnapshotId': self.snap1_id, 'VolumeSize': 4, 'VolumeType': 'io1', 'Iops': 100}}]).response.Image
        self.image_id = ret.ImageId
        assert self.image_id.startswith('ami-')
        assert len(ret.BlockDeviceMappings) == 1
        assert ret.BlockDeviceMappings[0].DeviceName == '/dev/sda1'
        assert ret.BlockDeviceMappings[0].Bsu.DeleteOnVmDeletion
        assert ret.BlockDeviceMappings[0].Bsu.SnapshotId.startswith('snap-')
        assert hasattr(ret.BlockDeviceMappings[0].Bsu, 'VolumeSize')
        assert ret.BlockDeviceMappings[0].Bsu.VolumeType == 'io1'
        assert ret.BlockDeviceMappings[0].Bsu.Iops == 100
        assert ret.FileLocation is not ''

    def test_T2325_from_snap_valid_bdm_virtual_device(self):
        ret = self.a1_r1.oapi.CreateImage(
            ImageName=self.ami_name, RootDeviceName='/dev/sda1', BlockDeviceMappings=[
                {'DeviceName': '/dev/sda1', 'Bsu': {'SnapshotId': self.snap1_id, 'DeleteOnVmDeletion': True}},
                {'DeviceName': '/dev/sdb', 'VirtualDeviceName': 'ephemeral1'}]).response.Image
        self.image_id = ret.ImageId
        assert self.image_id.startswith('ami-')
        assert len(ret.BlockDeviceMappings) == 1
        assert ret.BlockDeviceMappings[0].DeviceName == '/dev/sda1'
        assert ret.BlockDeviceMappings[0].Bsu.DeleteOnVmDeletion
        assert ret.BlockDeviceMappings[0].Bsu.SnapshotId == self.snap1_id
        assert ret.FileLocation is not ''

    # @pytest.mark.skip('disabled - Needs to be rewritten')
    # def test_T2326_from_snap_valid_bdm_virtual_and_2_physical_device(self):
    #    ret = self.a1_r1.oapi.CreateImage(
    #        ImageName=self.ami_name, RootDeviceName='/dev/sda1', BlockDeviceMappings=[
    #            {'DeviceName': '/dev/sda1', 'Bsu': {'SnapshotId': self.snap1_id, 'DeleteOnVmDeletion': False}},
    #            {'DeviceName': '/dev/sdb', 'VirtualDeviceName': 'ephemeral1'},
    #            {'DeviceName': '/dev/sdc', 'Bsu': {'VolumeSize': 2, 'DeleteOnVmDeletion': True}}]).response.Image
    #    self.image_id = ret.ImageId
    #    assert self.image_id.startswith('ami-')
    #    assert len(ret.BlockDeviceMappings) == 2
    #    assert ret.BlockDeviceMappings[0].DeviceName == '/dev/sda1'
    #    assert not ret.BlockDeviceMappings[1].Bsu.DeleteOnVmDeletion
    #    assert ret.BlockDeviceMappings[1].DeviceName == '/dev/sdc'
    #    assert ret.BlockDeviceMappings[1].Bsu.DeleteOnVmDeletion
    #    assert hasattr(ret.BlockDeviceMappings[1].Bsu, 'VolumeSize')
    #    assert ret.FileLocation is not ''

    def test_T2327_from_snap_bdm_iops_with_volume_standard(self):
        try:
            self.a1_r1.oapi.CreateImage(ImageName=self.ami_name, RootDeviceName='/dev/sda1', BlockDeviceMappings=[
                {'DeviceName': '/dev/sda1', 'Bsu': {'SnapshotId': self.snap1_id, 'Iops': 100}}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045', None)

    def test_T2328_from_snap_bdm_with_snap_and_virtual(self):
        try:
            self.a1_r1.oapi.CreateImage(ImageName=self.ami_name, RootDeviceName='/dev/sda1', BlockDeviceMappings=[
                {'DeviceName': '/dev/sda1', 'Bsu': {'SnapshotId': self.snap1_id}, 'VirtualDeviceName': '/dev/sda1'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4076', None)

    def test_T2329_from_snap_bdm_without_snap(self):
        try:
            self.a1_r1.oapi.CreateImage(ImageName=self.ami_name, RootDeviceName='/dev/sda1', BlockDeviceMappings=[
                {'DeviceName': '/dev/sda1', 'Bsu': {'VolumeSize': 2}}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7003', None)

    def test_T2330_from_snap_bdm_without_snap_with_virtual(self):
        try:
            self.a1_r1.oapi.CreateImage(ImageName=self.ami_name, RootDeviceName='/dev/sda1', BlockDeviceMappings=[
                {'DeviceName': '/dev/sda1', 'VirtualDeviceName': 'ephemeral1'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7003', None)

    def test_T4576_from_instance_with_additional_volume(self):
        self.image_id = self.a1_r1.oapi.CreateImage(VmId=self.inst_id2, ImageName=self.ami_name).response.Image.ImageId
        assert self.image_id.startswith('ami-')
        wait_images_state(self.a1_r1, [self.image_id], state='available')
        ret = self.a1_r1.oapi.ReadImages(Filters={'ImageIds': [self.image_id]}).response
        assert ret.Images and len(ret.Images) == 1
        assert ret.Images[0].BlockDeviceMappings and len(ret.Images[0].BlockDeviceMappings) == 2
