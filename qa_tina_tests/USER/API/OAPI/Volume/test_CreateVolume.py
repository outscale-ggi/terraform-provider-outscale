
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_dry_run
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state
from qa_tina_tests.USER.API.OAPI.Volume.Volume import validate_volume_response


class Test_CreateVolume(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vol_ids = None
        super(Test_CreateVolume, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateVolume, cls).teardown_class()

    def setup_method(self, method):
        super(Test_CreateVolume, self).setup_method(method)
        self.vol_ids = []

    def teardown_method(self, method):
        try:
            for volid in self.vol_ids:
                self.a1_r1.oapi.DeleteVolume(VolumeId=volid)
            self.vol_ids = []
        finally:
            super(Test_CreateVolume, self).teardown_method(method)

    def test_T2250_valid_params(self):
        ret = self.a1_r1.oapi.CreateVolume(SubregionName=self.azs[0], Size=2).response.Volume
        self.vol_ids.append(ret.VolumeId)
        validate_volume_response(ret, az=self.azs[0], volume_type='standard')

    def test_T2251_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.CreateVolume(SubregionName=self.azs[0], Size=10, DryRun=True)
        assert_dry_run(ret)

    def test_T3040_only_subregion(self):
        try:
            self.a1_r1.oapi.CreateVolume(SubregionName=self.azs[0])
        except Exception as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2949_missing_param(self):
        try:
            self.a1_r1.oapi.CreateVolume()
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateVolume(Size=2)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateVolume(Iops=10)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateVolume(SnapshotId='snap-12345678')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateVolume(VolumeType='standard')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2950_missing_size_or_snapshot_param(self):
        try:
            self.a1_r1.oapi.CreateVolume(SubregionName=self.azs[0])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2951_invalid_subregion(self):
        try:
            self.a1_r1.oapi.CreateVolume(Size=2, SubregionName='alpha')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5009')

    def test_T2952_invalid_size(self):
        try:
            self.a1_r1.oapi.CreateVolume(Size=-1, SubregionName=self.azs[0])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T2953_invalid_snapshot_id(self):
        try:
            self.a1_r1.oapi.CreateVolume(SnapshotId='tata', SubregionName=self.azs[0])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2954_unknown_snapshot_id(self):
        try:
            self.a1_r1.oapi.CreateVolume(SnapshotId='snap-12345678', SubregionName=self.azs[0])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5054')

    def test_T2955_malformed_snapshot_id(self):
        try:
            self.a1_r1.oapi.CreateVolume(SnapshotId='snap-123456', SubregionName=self.azs[0])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')

    def test_T2956_unknown_volume_type(self):
        try:
            self.a1_r1.oapi.CreateVolume(Size=2, VolumeType='mytype', SubregionName=self.azs[0])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2957_volume_type_gp2_invalid_size(self):
        try:
            ret = self.a1_r1.oapi.CreateVolume(VolumeType='gp2', SubregionName=self.azs[0],
                                               Size=92000).response.Volume
            self.vol_ids.append(ret.VolumeId)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T2958_volume_type_io1_invalid_size(self):
        try:
            ret = self.a1_r1.oapi.CreateVolume(VolumeType='io1', SubregionName=self.azs[0],
                                               Size=2, Iops=100).response.Volume
            self.vol_ids.append(ret.VolumeId)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T2959_volume_type_io1_invalid_iops(self):
        try:
            ret = self.a1_r1.oapi.CreateVolume(VolumeType='io1', SubregionName=self.azs[0],
                                               Size=4, Iops=1300).response.Volume
            self.vol_ids.append(ret.VolumeId)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')
        try:
            ret = self.a1_r1.oapi.CreateVolume(VolumeType='io1', SubregionName=self.azs[0],
                                               Size=4, Iops=99).response.Volume
            self.vol_ids.append(ret.VolumeId)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4029')
        try:
            ret = self.a1_r1.oapi.CreateVolume(VolumeType='io1', SubregionName=self.azs[0],
                                               Size=4, Iops=25).response.Volume
            self.vol_ids.append(ret.VolumeId)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4029')
        try:
            self.a1_r1.oapi.CreateVolume(VolumeType='io1', Size=4, Iops=-1, SubregionName=self.azs[0])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4029')

    def test_T2960_valid_volume_type(self):
        try:
            ret = self.a1_r1.oapi.CreateVolume(VolumeType='standard', SubregionName=self.azs[0], Size=2).response.Volume
            self.vol_ids.append(ret.VolumeId)
            validate_volume_response(ret, az=self.azs[0], volume_type='standard')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')
            assert False, 'Error should not occurs'
        try:
            ret = self.a1_r1.oapi.CreateVolume(VolumeType='gp2', SubregionName=self.azs[0], Size=2).response.Volume
            self.vol_ids.append(ret.VolumeId)
            validate_volume_response(ret, az=self.azs[0], volume_type='gp2')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')
            assert False, 'Error should not occurs'
        try:
            ret = self.a1_r1.oapi.CreateVolume(VolumeType='io1', SubregionName=self.azs[0],
                                               Size=4, Iops=100).response.Volume
            self.vol_ids.append(ret.VolumeId)
            validate_volume_response(ret, az=self.azs[0], volume_type='io1')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')
            assert False, 'Error should not occurs'

    def test_T2961_valid_from_snapshot_id_of_volume_standard(self):
        snap_id = None
        try:
            ret = self.a1_r1.oapi.CreateVolume(VolumeType='standard', SubregionName=self.azs[0], Size=2).response.Volume
            self.vol_ids.append(ret.VolumeId)
            wait_volumes_state(self.a1_r1, [ret.VolumeId], state='available')
            ret_snap = self.a1_r1.oapi.CreateSnapshot(VolumeId=ret.VolumeId).response.Snapshot
            snap_id = ret_snap.SnapshotId
            ret_vol2 = self.a1_r1.oapi.CreateVolume(SnapshotId=snap_id, SubregionName=self.azs[0]).response.Volume
            self.vol_ids.append(ret_vol2.VolumeId)
            validate_volume_response(ret_vol2, az=self.azs[0], volume_type='standard', snapshot_id=snap_id)
        finally:
            if snap_id:
                self.a1_r1.oapi.DeleteSnapshot(SnapshotId=snap_id)

    def test_T5231_valid_from_snapshot_id_of_volume_standard_with_an_inferior_size(self):
        snap_id = None
        ret_vol2 = None
        try:
            ret = self.a1_r1.oapi.CreateVolume(VolumeType='standard', SubregionName=self.azs[0], Size=2).response.Volume
            self.vol_ids.append(ret.VolumeId)
            wait_volumes_state(self.a1_r1, [ret.VolumeId], state='available')
            ret_snap = self.a1_r1.oapi.CreateSnapshot(VolumeId=ret.VolumeId).response.Snapshot
            snap_id = ret_snap.SnapshotId
            ret_vol2 = self.a1_r1.oapi.CreateVolume(SnapshotId=snap_id, SubregionName=self.azs[0], Size=1).response.Volume
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', 4125)
        finally:
            if ret_vol2:
                self.a1_r1.oapi.DeleteVolume(VolumeId=ret_vol2.VolumeId)
            if snap_id:
                self.a1_r1.oapi.DeleteSnapshot(SnapshotId=snap_id)

    def test_T2962_valid_from_snapshot_id_of_volume_gp2(self):
        snap_id = None
        try:
            ret = self.a1_r1.oapi.CreateVolume(VolumeType='gp2', SubregionName=self.azs[0], Size=2).response.Volume
            self.vol_ids.append(ret.VolumeId)
            wait_volumes_state(self.a1_r1, [ret.VolumeId], state='available')
            ret_snap = self.a1_r1.oapi.CreateSnapshot(VolumeId=ret.VolumeId).response.Snapshot
            snap_id = ret_snap.SnapshotId
            ret_vol2 = self.a1_r1.oapi.CreateVolume(SnapshotId=snap_id, SubregionName=self.azs[0]).response.Volume
            self.vol_ids.append(ret_vol2.VolumeId)
            validate_volume_response(ret_vol2, az=self.azs[0], volume_type='standard', snapshot_id=snap_id)
        finally:
            if snap_id:
                self.a1_r1.oapi.DeleteSnapshot(SnapshotId=snap_id)

    def test_T2963_valid_from_snapshot_id_of_volume_io1(self):
        snap_id = None
        try:
            ret = self.a1_r1.oapi.CreateVolume(VolumeType='io1', SubregionName=self.azs[0], Size=4, Iops=100).response.Volume
            self.vol_ids.append(ret.VolumeId)
            wait_volumes_state(self.a1_r1, [ret.VolumeId], state='available')
            ret_snap = self.a1_r1.oapi.CreateSnapshot(VolumeId=ret.VolumeId).response.Snapshot
            snap_id = ret_snap.SnapshotId
            ret_vol2 = self.a1_r1.oapi.CreateVolume(SnapshotId=snap_id, SubregionName=self.azs[0]).response.Volume
            self.vol_ids.append(ret_vol2.VolumeId)
            validate_volume_response(ret_vol2, az=self.azs[0], volume_type='standard', snapshot_id=snap_id)
        finally:
            if snap_id:
                self.a1_r1.oapi.DeleteSnapshot(SnapshotId=snap_id)
