
import datetime

import pytest

from specs import check_tools
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina import wait_tools
from qa_tina_tests.USER.API.OAPI.Volume.Volume import validate_volume_response


@pytest.mark.region_oapi
class Test_ReadVolumes(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.vol_ids = []
        cls.snap_id = None
        cls.vms = None
        super(Test_ReadVolumes, cls).setup_class()
        try:
            cls.vol_ids.append(cls.a1_r1.oapi.CreateVolume(VolumeType='standard', Size=2, SubregionName=cls.azs[0]).response.Volume.VolumeId)
            cls.vol_ids.append(cls.a1_r1.oapi.CreateVolume(VolumeType='gp2', Size=2, SubregionName=cls.azs[0]).response.Volume.VolumeId)
            if cls.a1_r1.config.region.az_name != 'in-west-1b':
                cls.vol_ids.append(cls.a1_r1.oapi.CreateVolume(VolumeType='io1', Size=4, Iops=100, SubregionName=cls.azs[0]).response.Volume.VolumeId)
            cls.vol_ids.append(cls.a1_r1.oapi.CreateVolume(Size=20, SubregionName=cls.azs[0]).response.Volume.VolumeId)
            wait_tools.wait_volumes_state(cls.a1_r1, cls.vol_ids, state='available')
            cls.snap_id = cls.a1_r1.oapi.CreateSnapshot(VolumeId=cls.vol_ids[0]).response.Snapshot.SnapshotId
            wait_tools.wait_snapshots_state(cls.a1_r1, [cls.snap_id], state='completed')
            cls.vol_ids.append(cls.a1_r1.oapi.CreateVolume(SnapshotId=cls.snap_id, SubregionName=cls.azs[0]).response.Volume.VolumeId)
            image_id = cls.a1_r1.config.region.get_info(constants.CENTOS_LATEST)
            cls.vms = cls.a1_r1.oapi.CreateVms(ImageId=image_id,
                                               VmType=cls.a1_r1.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE)).response.Vms
            wait_tools.wait_instances_state(cls.a1_r1, [cls.vms[0].VmId], state='running')
        except Exception:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            for vol_id in cls.vol_ids:
                cls.a1_r1.oapi.DeleteVolume(VolumeId=vol_id)
            if cls.snap_id:
                cls.a1_r1.oapi.DeleteSnapshot(SnapshotId=cls.snap_id)
            if cls.vms:
                try:
                    cls.a1_r1.oapi.DeleteVms(VmIds=[cls.vms[0].VmId])
                    wait_tools.wait_instances_state(cls.a1_r1, [cls.vms[0].VmId], state='terminated')
                except:
                    print('Could not delete instances')
        finally:
            super(Test_ReadVolumes, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T2248_valid_params(self):
        ret = self.a1_r1.oapi.ReadVolumes()
        ret.check_response()
        assert len(ret.response.Volumes) == len(self.vol_ids) + 1
        for volume in ret.response.Volumes:
            validate_volume_response(volume)

    def test_T2249_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadVolumes(DryRun=True)
        misc.assert_dry_run(ret)

    def test_T2968_filters_volume_type_standard(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeTypes': ['standard']}).response.Volumes
        assert len(ret) == 4
        for volume in ret:
            validate_volume_response(volume, vol_type='standard')

    def test_T2969_filters_volume_type_gp2(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeTypes': ['gp2']}).response.Volumes
        assert len(ret) == 1
        for volume in ret:
            validate_volume_response(volume, vol_type='gp2')

    def test_T2970_filters_volume_type_io1(self):
        if self.a1_r1.config.region.az_name == 'in-west-1b':
            pytest.skip("In-west-1b does not support io1 storage")
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeTypes': ['io1']}).response.Volumes
        assert len(ret) == 1
        for volume in ret:
            validate_volume_response(volume, vol_type='io1')

    def test_T2971_filters_volume_type_unknown(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeTypes': ['unknown']}).response.Volumes
        assert len(ret) == 0

    def test_T2972_filters_snap_id(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'SnapshotIds': [self.snap_id]}).response.Volumes
        assert len(ret) == 1
        for volume in ret:
            validate_volume_response(volume, snapshot_id=self.snap_id)

    def test_T2973_filters_snap_id_invalid(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'SnapshotIds': ['tata']}).response.Volumes
        assert len(ret) == 0

    def test_T2974_filters_snap_id_unknown(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'SnapshotIds': ['snap-12345678']}).response.Volumes
        assert len(ret) == 0

    def test_T6091_filters_snap_id_valid_value(self):
        with pytest.raises(OscApiException) as error:
            self.a1_r1.oapi.ReadVolumes(Filters={'SnapshotIds': self.snap_id})
        check_tools.check_oapi_error(error.value, 4110)

    def test_T6089_filters_snap_id_empty_list(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'SnapshotIds': []}).response.Volumes
        assert len(ret) == 0

    def test_T6090_filters_snap_id_none(self):
        with pytest.raises(OscApiException) as error:
            self.a1_r1.oapi.ReadVolumes(Filters={'SnapshotIds': None})
        check_tools.check_oapi_error(error.value, 4110)

    def test_T2975_filters_malformed_unknown(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'SnapshotIds': ['snap-123456']}).response.Volumes
        assert len(ret) == 0

    def test_T2976_filters_volume_id(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeIds': [self.vol_ids[1]]}).response.Volumes
        assert len(ret) == 1
        for volume in ret:
            validate_volume_response(volume, volume_id=self.vol_ids[1])

    def test_T2977_filters_multiple_volume_ids(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeIds': [self.vol_ids[1], self.vol_ids[3]]}).response.Volumes
        assert len(ret) == 2
        for volume in ret:
            validate_volume_response(volume)

    def test_T2978_filters_volume_id_invalid(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeIds': ['tata']}).response.Volumes
        assert len(ret) == 0

    def test_T2979_filters_volume_id_malformed(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeIds': ['vol-123456']}).response.Volumes
        assert len(ret) == 0

    def test_T2980_filters_volume_id_unknown(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeIds': ['vol-12345678']}).response.Volumes
        assert len(ret) == 0

    def test_T2981_filters_subregion_name_invalid(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'SubregionNames': ['tata']}).response.Volumes
        assert len(ret) == 0

    def test_T2982_filters_subregion_name(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'SubregionNames': [self.azs[0]]}).response.Volumes
        assert len(ret) == len(self.vol_ids) + 1

    def test_T2983_filters_volume_state(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeStates': ['in-use']}).response.Volumes
        for volume in ret:
            validate_volume_response(volume, state='in-use')
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeStates': ['available']}).response.Volumes
        for volume in ret:
            validate_volume_response(volume, state='available')

    def test_T2984_filters_volume_state_invalid(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeStates': ['helloworld']}).response.Volumes
        assert len(ret) == 0

    @pytest.mark.tag_sec_confidentiality
    def test_T3443_with_other_account(self):
        ret = self.a2_r1.oapi.ReadVolumes().response.Volumes
        assert not ret

    @pytest.mark.tag_sec_confidentiality
    def test_T3444_with_other_account_filters(self):
        ret = self.a2_r1.oapi.ReadVolumes(Filters={'VolumeIds': [self.vol_ids[1], self.vol_ids[3]]}).response.Volumes
        assert not ret

    def test_T3560_filters_link_delete_on_termination_true(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'LinkVolumeDeleteOnVmDeletion': True}).response.Volumes
        assert len(ret) == 1
        for volume in ret:
            validate_volume_response(volume, linked_volume={'DeleteOnVmDeletion': True})

    def test_T3561_filters_link_delete_on_termination_false(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'LinkVolumeDeleteOnVmDeletion': False}).response.Volumes
        assert len(ret) == 0

    def test_T3562_filters_link_device_names(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'LinkVolumeDeviceNames': ['/dev/sda1']}).response.Volumes
        assert len(ret) == 1
        for volume in ret:
            validate_volume_response(volume, linked_volume={'DeviceName': '/dev/sda1'})

    def test_T3563_filters_link_dates(self):
        ret = self.a1_r1.oapi.ReadVolumes(
            Filters={'LinkVolumeLinkDates': [datetime.datetime(2019, 2, 4, 7, 56, 19, 749052).strftime("%Y-%m-%dT%H:%M:%SZ")]}).response.Volumes
        assert len(ret) == 0

    def test_T3564_filters_link_states(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'LinkVolumeLinkStates': ['attached']}).response.Volumes
        assert len(ret) == 1
        for volume in ret:
            validate_volume_response(volume, linked_volume={'State': 'attached'})

    def test_T3565_filters_link_vm_ids(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'LinkVolumeVmIds': [self.vms[0].VmId]}).response.Volumes
        assert len(ret) == 1
        for volume in ret:
            validate_volume_response(volume, linked_volume={'State': 'attached', 'VmId': self.vms[0].VmId})

    def test_T3748_filters_volume_sizes(self):
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeSizes': [2]}).response.Volumes
        assert len(ret) == 3
        for volume in ret:
            validate_volume_response(volume, size=2)
        ret = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeSizes': [20]}).response.Volumes
        assert len(ret) == 1
        for volume in ret:
            validate_volume_response(volume, size=20)

    def test_T5983_with_tag_filter(self):
        indexes, _ = misc.execute_tag_tests(self.a1_r1, 'Volume', self.vol_ids, 'oapi.ReadVolumes', 'Volumes.VolumeId')
        assert indexes == [6, 24, 25, 26, 27, 28, 29]
        known_error('API-399', 'ReadVolumes does not support wildcards filtering')
