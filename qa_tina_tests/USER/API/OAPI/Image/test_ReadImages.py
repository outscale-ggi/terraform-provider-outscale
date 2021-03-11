# -*- coding:utf-8 -*-
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.exceptions import OscTestException
from qa_test_tools.misc import assert_oapi_error, id_generator
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_volumes
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state


class Test_ReadImages(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadImages, cls).setup_class()
        cls.image_id = None
        cls.image_id2 = None
        cls.image_id3 = None
        cls.snap1_id = None
        cls.volume_ids = None
        try:
            image_id = cls.a1_r1.config.region.get_info(constants.CENTOS7)
            cls.image_id = cls.a1_r1.oapi.CreateImage(SourceImageId=image_id, SourceRegionName=cls.a1_r1.config.region.name,
                                                      ImageName='test').response.Image.ImageId
            cls.image_id2 = cls.a1_r1.oapi.CreateImage(SourceImageId=image_id, SourceRegionName=cls.a1_r1.config.region.name,
                                                       ImageName='test1').response.Image.ImageId
            cls.image_id3 = cls.a1_r1.oapi.CreateImage(SourceImageId=image_id, SourceRegionName=cls.a1_r1.config.region.name,
                                                       ImageName='test2', Description='my description').response.Image.ImageId
            cls.a1_r1.oapi.UpdateImage(ImageId=cls.image_id2,
                                       PermissionsToLaunch={'Additions': {'AccountIds': [cls.a2_r1.config.account.account_id]}})
            cls.a1_r1.oapi.UpdateImage(ImageId=cls.image_id3,
                                       PermissionsToLaunch={'Removals': {'GlobalPermission': True}})
            _, cls.volume_ids = create_volumes(cls.a1_r1, size=2)
            wait_volumes_state(cls.a1_r1, cls.volume_ids, state='available')
            cls.snap1_id = cls.a1_r1.oapi.CreateSnapshot(VolumeId=cls.volume_ids[0]).response.Snapshot.SnapshotId
            cls.ami_name = id_generator(prefix='imgname ')
            cls.image_id4 = cls.a1_r1.oapi.CreateImage(ImageName=cls.ami_name, RootDeviceName='/dev/sda1', BlockDeviceMappings=[
                {'DeviceName': '/dev/sda1',
                 'Bsu': {'SnapshotId': cls.snap1_id, 'VolumeSize': 4, 'VolumeType': 'io1', 'Iops': 100}}]).response.Image.ImageId
            # to be clear permission on image_id :
            #           - AccountIds = []
            #           - GlobalPermission = True
            # to be clear permission on image_id2 :
            #           - AccountIds = [a2_r1...account_id]
            #           - GlobalPermission = True
            # to be clear permission on image_id3 :
            #           - AccountIds = []
            #           - GlobalPermission = False
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    @classmethod
    def teardown_class(cls):
        errors = []
        try:
            if cls.image_id:
                try:
                    cls.a1_r1.oapi.DeleteImage(ImageId=cls.image_id)
                except Exception as error:
                    errors.append(error)
            if cls.image_id2:
                try:
                    cls.a1_r1.oapi.DeleteImage(ImageId=cls.image_id2)
                except Exception as error:
                    errors.append(error)
            if cls.image_id3:
                try:
                    cls.a1_r1.oapi.DeleteImage(ImageId=cls.image_id3)
                except Exception as error:
                    errors.append(error)
            if cls.image_id4:
                try:
                    cls.a1_r1.oapi.DeleteImage(ImageId=cls.image_id4)
                except Exception as error:
                    errors.append(error)
            if cls.snap1_id:
                try:
                    cls.a1_r1.oapi.DeleteSnapshot(SnapshotId=cls.snap1_id)
                except Exception as error:
                    errors.append(error)
            if cls.volume_ids:
                delete_volumes(cls.a1_r1, cls.volume_ids)
            if errors:
                raise OscTestException('Found {} errors while cleaning resources : \n{}'.format(len(errors), errors))
        finally:
            super(Test_ReadImages, cls).teardown_class()

    def test_T2304_empty_filters(self):
        ret = self.a1_r1.oapi.ReadImages().response.Images
        assert len(ret) >= 3
        image = next((i for i in ret if i.ImageId == self.image_id), None)
        assert image.AccountId == self.a1_r1.config.account.account_id
        assert image.Architecture == 'x86_64'
        assert len(image.BlockDeviceMappings) == 1
        assert image.BlockDeviceMappings[0].DeviceName == '/dev/sda1'
        assert image.BlockDeviceMappings[0].Bsu.DeleteOnVmDeletion
        assert image.BlockDeviceMappings[0].Bsu.SnapshotId.startswith('snap-')
        assert hasattr(image.BlockDeviceMappings[0].Bsu, 'VolumeSize')
        assert image.BlockDeviceMappings[0].Bsu.VolumeType == 'standard'
        assert image.FileLocation != ''
        assert image.PermissionsToLaunch.GlobalPermission
        assert image.PermissionsToLaunch.AccountIds == []
        assert image.ProductCodes is not None
        assert image.RootDeviceName == '/dev/sda1'
        assert image.RootDeviceType == 'bsu'
        assert image.State == 'available'
        assert image.StateComment is not None
        assert image.Tags == []
        assert image is not None

    def test_T2305_filters_account_ids(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'AccountIds': [self.a1_r1.config.account.account_id]}).response.Images
        assert len(ret) == 4
        for img in ret:
            assert img.AccountId == self.a1_r1.config.account.account_id

    def test_T2306_filters_image_id(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'ImageIds': [self.image_id]}).response.Images
        assert len(ret) == 1
        assert ret[0].ImageId == self.image_id

    def test_T5545_filters_hypervisors(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'Hypervisors': ['xen']})
        assert len(ret.response.Images) >= 3
        #TODO add the verify response
        # verify_response(ret.response, os.path.join(os.path.dirname(os.path.abspath(__file__)),
        #                                                   'read_image_hypervisors_filter.json'),
        #                        None), 'Could not verify response content.'

    def test_T5546_filters_productscode(self):
        try:
            ret = self.a1_r1.oapi.ReadImages(Filters={'ProductCodes': ['0001']})
            assert len(ret.response.Images) >= 3
            assert False, 'Remove known error'
        except AssertionError:
            known_error('GTW-1763', 'ProductCodes filter does not work in ReadImages')

    def test_T2307_filters_states_pending(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'States': ['pending/queued']}).response.Images
        assert len(ret) >= 0
        if len(ret) > 0:
            assert ret[0].State == 'pending/queued'

    def test_T2308_filters_states_completed(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'States': ['completed']}).response.Images
        assert len(ret) >= 0
        if len(ret) > 0:
            assert ret[0].State == 'completed'

    def test_T2309_filters_a1_permissions_account_a1(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'PermissionsToLaunchAccountIds': [self.a1_r1.config.account.account_id]}).response.Images
        assert len(ret) == 0

    def test_T2310_filters_a1_permissions_account_a2(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'PermissionsToLaunchAccountIds': [self.a2_r1.config.account.account_id]}).response.Images
        assert len(ret) == 1
        assert len(ret[0].PermissionsToLaunch.AccountIds) == 1
        assert ret[0].PermissionsToLaunch.AccountIds[0] == self.a2_r1.config.account.account_id

    def test_T2311_filters_a2_permissions_account_a1(self):
        ret = self.a2_r1.oapi.ReadImages(Filters={'PermissionsToLaunchAccountIds': [self.a1_r1.config.account.account_id]}).response.Images
        assert len(ret) == 0

    def test_T2312_filters_a2_permissions_account_a2(self):
        ret = self.a2_r1.oapi.ReadImages(Filters={'PermissionsToLaunchAccountIds': [self.a2_r1.config.account.account_id]}).response.Images
        assert len(ret) == 1

    def test_T2313_filters_a1_permissions_global_permission_true(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'PermissionsToLaunchGlobalPermission': True}).response.Images
        assert len(ret) >= 2
        for image in ret:
            assert image.PermissionsToLaunch.GlobalPermission

    def test_T2314_filters_a1_permissions_global_permission_false(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'PermissionsToLaunchGlobalPermission': False}).response.Images
        for image in ret:
            assert not image.PermissionsToLaunch.GlobalPermission

    def test_T2315_filters_a1_permissions_global_permission_true_false(self):
        try:
            self.a1_r1.oapi.ReadImages(Filters={'PermissionsToLaunchGlobalPermission': [True, False]})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110', None)

    def test_T2316_filters_a1_permissions_global_permission_and_accounts_ids(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={
            'PermissionsToLaunchGlobalPermission': True,
            'PermissionsToLaunchAccountIds': [self.a2_r1.config.account.account_id]
        }).response.Images
        assert len(ret) == 1
        assert ret[0].PermissionsToLaunch.GlobalPermission
        assert len(ret[0].PermissionsToLaunch.AccountIds) == 1
        assert ret[0].PermissionsToLaunch.AccountIds[0] == self.a2_r1.config.account.account_id

    def test_T3385_filters_image_names(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'ImageNames': [self.ami_name]}).response.Images
        assert len(ret) == 1
        assert ret[0].ImageId == self.image_id4
        assert ret[0].ImageName == self.ami_name

    def test_T3386_filters_descriptions(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'Descriptions': ['my description']}).response.Images
        assert len(ret) == 1
        assert ret[0].ImageId == self.image_id3
        assert ret[0].Description == 'my description'

    def test_T3387_filters_architectures(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'Architectures': ['x86_64']}).response.Images
        for i in ret:
            assert i.Architecture == 'x86_64'

    def test_T3388_filters_block_device_mapping_delete_on_vm_deletion_true(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'BlockDeviceMappingDeleteOnVmDeletion': True}).response.Images
        for i in ret:
            found = False
            for bdm in i.BlockDeviceMappings:
                if bdm.Bsu.DeleteOnVmDeletion:
                    found = True
            assert found

    def test_T3389_filters_block_device_mapping_delete_on_vm_deletion_false(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'BlockDeviceMappingDeleteOnVmDeletion': False}).response.Images
        for i in ret:
            found = False
            for bdm in i.BlockDeviceMappings:
                if not bdm.Bsu.DeleteOnVmDeletion:
                    found = True
            assert found

    def test_T3390_filters_block_device_mapping_device_names(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'BlockDeviceMappingDeviceNames': ['/dev/sda1']}).response.Images
        for i in ret:
            found = False
            for bdm in i.BlockDeviceMappings:
                if bdm.DeviceName == '/dev/sda1':
                    found = True
            assert found

    def test_T3391_filters_block_device_mapping_snapshot_ids(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'BlockDeviceMappingSnapshotIds': [self.snap1_id]}).response.Images
        for i in ret:
            found = False
            for bdm in i.BlockDeviceMappings:
                if bdm.Bsu.SnapshotId == self.snap1_id:
                    found = True
            assert found

    def test_T3392_filters_block_device_mapping_volume_sizes(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'BlockDeviceMappingVolumeSizes': [2]}).response.Images
        for i in ret:
            found = False
            for bdm in i.BlockDeviceMappings:
                if bdm.Bsu.VolumeSize == 2:
                    found = True
            assert found

    def test_T3393_filters_block_device_mapping_volume_types(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'BlockDeviceMappingVolumeTypes': ['gp2']}).response.Images
        for i in ret:
            found = False
            for bdm in i.BlockDeviceMappings:
                if bdm.Bsu.VolumeType == 'gp2':
                    found = True
            assert found

    def test_T3394_filters_file_locations(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'FileLocations': ['*centos-6-copy*']}).response.Images
        for i in ret:
            assert 'centos-6-copy' in i.FileLocation

    def test_T3395_filters_root_device_names(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'RootDeviceNames': ['/dev/sda1']}).response.Images
        for i in ret:
            assert i.RootDeviceName == '/dev/sda1'

    def test_T3396_filters_root_device_types(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'RootDeviceTypes': ['bsu']}).response.Images
        for i in ret:
            assert i.RootDeviceType == 'bsu'

    def test_T3397_filters_virtualization_types(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'VirtualizationTypes': ['hvm']}).response.Images
        assert len(ret) > 4

    @pytest.mark.tag_sec_confidentiality
    def test_T3411_other_account(self):
        ret = self.a2_r1.oapi.ReadImages().response.Images
        assert self.image_id3 not in [img.ImageId for img in ret]

    @pytest.mark.tag_sec_confidentiality
    def test_T3412_other_account_with_filter(self):
        ret = self.a2_r1.oapi.ReadImages(Filters={'AccountIds': [self.a1_r1.config.account.account_id]}).response.Images
        assert len(ret) == 2

    def test_T3738_filters_accountaliases(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'AccountAliases': ['titi']}).response.Images
        assert not ret

    def test_T3739_filters_imagenames(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'ImageNames': ['test']}).response.Images
        assert len(ret) == 1
        assert ret[0].ImageId == self.image_id

    def test_T4513_filters_outscale_imageids(self):
        ret = self.a1_r1.oapi.ReadImages(Filters={'ImageIds': [self.a1_r1.config.region.get_info(constants.CENTOS7)]}).response.Images
        assert len(ret) == 1
        assert ret[0].AccountAlias == "Outscale"
        assert ret[0].AccountId
        assert ret[0].Architecture == 'x86_64'
        assert len(ret[0].BlockDeviceMappings) == 1
        assert ret[0].BlockDeviceMappings[0].DeviceName == '/dev/sda1'
        assert ret[0].BlockDeviceMappings[0].Bsu.DeleteOnVmDeletion
        assert ret[0].BlockDeviceMappings[0].Bsu.SnapshotId.startswith('snap-')
        assert hasattr(ret[0].BlockDeviceMappings[0].Bsu, 'VolumeSize')
        assert ret[0].BlockDeviceMappings[0].Bsu.VolumeType == 'standard'
        assert ret[0].CreationDate
        assert hasattr (ret[0], 'Description')
        assert ret[0].FileLocation
        assert ret[0].ImageId == self.a1_r1.config.region.get_info(constants.CENTOS7)
        assert ret[0].ImageName
        assert ret[0].PermissionsToLaunch.GlobalPermission
        assert ret[0].PermissionsToLaunch.AccountIds
        assert ret[0].ProductCodes is not None
        assert ret[0].RootDeviceName == '/dev/sda1'
        assert ret[0].RootDeviceType == 'bsu'
        assert ret[0].State == 'available'
        assert ret[0].StateComment
        assert hasattr(ret[0], 'Tags')
        assert hasattr(ret[0], 'ImageType')
