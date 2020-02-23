# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

import pytest

from osc_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tests.USER.API.OAPI.Snapshot.Snapshot import Snapshot
from qa_tina_tools.constants import CODE_INJECT
from qa_common_tools.misc import assert_oapi_error
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state


class Test_CreateSnapshot(Snapshot):

    def setup_method(self, method):
        super(Test_CreateSnapshot, self).setup_method(method)
        self.snap_ids = []

    def teardown_method(self, method):
        try:
            for snap_id in self.snap_ids:
                self.a1_r1.oapi.DeleteSnapshot(SnapshotId=snap_id)
            wait_snapshots_state(self.a1_r1, self.snap_ids, cleanup=True)
        finally:
            super(Test_CreateSnapshot, self).teardown_method(method)

    def test_T2179_empty_param(self):
        try:
            self.a1_r1.oapi.CreateSnapshot()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    def test_T2756_invalid_combination(self):
        try:
            self.a1_r1.oapi.CreateSnapshot(VolumeId=self.volume_id1, SourceRegionName=self.a1_r1.config.region.name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)
        try:
            self.a1_r1.oapi.CreateSnapshot(VolumeId=self.volume_id1, SourceSnapshotId='snap-123456789')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)
        try:
            self.a1_r1.oapi.CreateSnapshot(VolumeId=self.volume_id1, SnapshotSize=1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)
        try:
            self.a1_r1.oapi.CreateSnapshot(VolumeId=self.volume_id1, SnapshotSize=1, FileLocation='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)
        try:
            self.a1_r1.oapi.CreateSnapshot(VolumeId=self.volume_id1, FileLocation='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)
        try:
            self.a1_r1.oapi.CreateSnapshot(FileLocation='foo', SourceRegionName=self.a1_r1.config.region.name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)
        try:
            self.a1_r1.oapi.CreateSnapshot(SnapshotSize=1, SourceRegionName=self.a1_r1.config.region.name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)
        try:
            self.a1_r1.oapi.CreateSnapshot(FileLocation='foo', SourceSnapshotId='snap-123456789')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)
        try:
            self.a1_r1.oapi.CreateSnapshot(SnapshotSize=1, SourceSnapshotId='snap-123456789')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)

    def test_T2180_invalid_volume_id(self):
        try:
            self.a1_r1.oapi.CreateSnapshot(VolumeId='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104', None)

    def test_T2181_unknown_volume_id(self):
        try:
            self.a1_r1.oapi.CreateSnapshot(VolumeId='vol-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5064', None)

    def test_T2182_valid_case_from_volume(self):
        ret = self.a1_r1.oapi.CreateSnapshot(VolumeId=self.volume_id1).response.Snapshot
        self.snap_ids.append(ret.SnapshotId)
        self.validate_snasphot(ret, expected_snap={
            'Description': '',
            'AccountId': self.a1_r1.config.account.account_id,
            'VolumeId': self.volume_id1,
            'VolumeSize': 2,
        })

    def test_T2183_valid_case_with_description(self):
        ret = self.a1_r1.oapi.CreateSnapshot(VolumeId=self.volume_id2, Description='hello').response.Snapshot
        self.snap_ids.append(ret.SnapshotId)
        self.validate_snasphot(ret, expected_snap={
            'Description': 'hello',
            'AccountId': self.a1_r1.config.account.account_id,
            'VolumeId': self.volume_id2,
            'VolumeSize': 4,
        })

    @pytest.mark.tag_sec_injection
    def test_T3818_code_injection_in_description(self):
        for desc in CODE_INJECT:
            ret = self.a1_r1.oapi.CreateSnapshot(VolumeId=self.volume_id2, Description=desc).response.Snapshot
            self.snap_ids.append(ret.SnapshotId)
            self.validate_snasphot(ret, expected_snap={
                'Description': desc,
                'AccountId': self.a1_r1.config.account.account_id,
                'VolumeId': self.volume_id2,
                'VolumeSize': 4,
            })

    @pytest.mark.tag_sec_confidentiality
    def test_T3817_other_account_volume_id(self):
        try:
            self.a2_r1.oapi.CreateSnapshot(VolumeId=self.volume_id2)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5064', None)

    def test_T2174_invalid_snapshot_id(self):
        try:
            self.a1_r1.oapi.CreateSnapshot(SourceSnapshotId='tata', SourceRegionName=self.a1_r1.config.region.name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104', None)

    def test_T2175_unknown_snapshot_id(self):
        try:
            self.a1_r1.oapi.CreateSnapshot(SourceSnapshotId='snap-12345678', SourceRegionName=self.a1_r1.config.region.name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5054', None)

    def test_T2176_unknown_region(self):
        try:
            self.a1_r1.oapi.CreateSnapshot(SourceSnapshotId='snap-12345678', SourceRegionName='alpha')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'OperationNotSupported', '8019', None)

    def test_T2177_valid_case_from_snapshot(self):
        id1 = self.a1_r1.oapi.CreateSnapshot(VolumeId=self.volume_id2, Description='hello').response.Snapshot.SnapshotId
        self.snap_ids.append(id1)
        wait_snapshots_state(self.a1_r1, self.snap_ids, state='completed')
        ret = self.a1_r1.oapi.CreateSnapshot(SourceSnapshotId=id1, SourceRegionName=self.a1_r1.config.region.name).response.Snapshot
        self.snap_ids.append(ret.SnapshotId)
        self.validate_snasphot(ret, expected_snap={
            'Description': 'hello',
            'AccountId': self.a1_r1.config.account.account_id,
            'VolumeSize': 4,
        })
        assert ret.SnapshotId != id1
        assert ret.Description == 'hello'
        assert isinstance(ret.Progress, int)
        assert ret.PermissionsToCreateVolume is not None
        assert ret.State is not None
        assert ret.VolumeSize == 4
