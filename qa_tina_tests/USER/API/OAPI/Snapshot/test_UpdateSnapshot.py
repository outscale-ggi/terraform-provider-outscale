# -*- coding:utf-8 -*-
import pytest

from osc_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tests.USER.API.OAPI.Snapshot.Snapshot import Snapshot
from qa_common_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state


class Test_UpdateSnapshot(Snapshot):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateSnapshot, cls).setup_class()
        cls.snap1_id = None
        try:
            cls.snap1_id = cls.a1_r1.oapi.CreateSnapshot(VolumeId=cls.volume_id1).response.Snapshot.SnapshotId
            cls.snap2_id = cls.a1_r1.oapi.CreateSnapshot(VolumeId=cls.volume_id2, Description='1..2..3').response.Snapshot.SnapshotId
            cls.snap3_id = cls.a1_r1.oapi.CreateSnapshot(VolumeId=cls.volume_id1, Description='4..5..6').response.Snapshot.SnapshotId
            wait_snapshots_state(cls.a1_r1, [cls.snap1_id, cls.snap2_id, cls.snap3_id], state='completed')
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.snap1_id:
                cls.a1_r1.oapi.DeleteSnapshot(SnapshotId=cls.snap1_id)
            if cls.snap2_id:
                cls.a1_r1.oapi.DeleteSnapshot(SnapshotId=cls.snap2_id)
            if cls.snap3_id:
                cls.a1_r1.oapi.DeleteSnapshot(SnapshotId=cls.snap3_id)
        finally:
            super(Test_UpdateSnapshot, cls).teardown_class()

    def test_T2198_empty_param(self):
        try:
            self.a1_r1.oapi.UpdateSnapshot()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    def test_T2199_invalid_snapshot_id(self):
        try:
            self.a1_r1.oapi.UpdateSnapshot(SnapshotId='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    def test_T2200_unknown_snaphot_id(self):
        try:
            self.a1_r1.oapi.UpdateSnapshot(SnapshotId='snap-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    def test_T2201_no_permissions(self):
        try:
            self.a1_r1.oapi.UpdateSnapshot(SnapshotId=self.snap2_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    def test_T2202_permission_addition_accountIds_valid(self):
        permissions = {'Additions': {'AccountIds': [self.a2_r1.config.account.account_id]}}
        self.a1_r1.oapi.UpdateSnapshot(SnapshotId=self.snap2_id, PermissionsToCreateVolume=permissions)

    def test_T2203_permission_addition_many_accountIds_valid(self):
        permissions = {'Additions': {'AccountIds': [self.a1_r1.config.account.account_id, self.a2_r1.config.account.account_id]}}
        self.a1_r1.oapi.UpdateSnapshot(SnapshotId=self.snap2_id, PermissionsToCreateVolume=permissions)

    def test_T2204_permission_addition_accountIds_invalid(self):
        try:
            permissions = {'Addition': {'AccountIds': ['tata']}}
            self.a1_r1.oapi.UpdateSnapshot(SnapshotId=self.snap2_id, PermissionsToCreateVolume=permissions)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001', None)

    def test_T2205_permission_addition_invalid_global_permissions(self):
        try:
            permissions = {'Additions': {'GlobalPermission': 'tata'}}
            self.a1_r1.oapi.UpdateSnapshot(SnapshotId=self.snap3_id, PermissionsToCreateVolume=permissions)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110', None)

    def test_T2206_permission_addition_global_permissions(self):
        permissions = {'Additions': {'GlobalPermission': True}}
        self.a1_r1.oapi.UpdateSnapshot(SnapshotId=self.snap3_id, PermissionsToCreateVolume=permissions)

    def test_T2207_permission_addition_accounts_and_global_permissions(self):
        permissions = {'Additions': {'GlobalPermission': True, 'AccountIds': [self.a2_r1.config.account.account_id]}}
        self.a1_r1.oapi.UpdateSnapshot(SnapshotId=self.snap3_id, PermissionsToCreateVolume=permissions)

    def test_T2208_permission_addition_and_removal_accountIds_invalid(self):
        try:
            permissions = {
                'Additions': {'AccountIds': [self.a2_r1.config.account.account_id]},
                'Removals': {'AccountIds': [self.a2_r1.config.account.account_id]}}
            self.a1_r1.oapi.UpdateSnapshot(SnapshotId=self.snap2_id, PermissionsToCreateVolume=permissions)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002', None)

    def test_T2209_permission_removal_accountIds_invalid(self):
        permissions = {'Removals': {'AccountIds': [self.a2_r1.config.account.account_id]}}
        self.a1_r1.oapi.UpdateSnapshot(SnapshotId=self.snap2_id, PermissionsToCreateVolume=permissions)

    def test_T2210_permission_removal_global_permissions(self):
        permissions = {'Removals': {'GlobalPermission': True}}
        self.a1_r1.oapi.UpdateSnapshot(SnapshotId=self.snap3_id, PermissionsToCreateVolume=permissions)

    def test_T3527_dry_run(self):
        permissions = {'Additions': {'AccountIds': [self.a2_r1.config.account.account_id]}}
        ret = self.a1_r1.oapi.UpdateSnapshot(SnapshotId=self.snap2_id, PermissionsToCreateVolume=permissions, DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3528_other_account(self):
        permissions = {'Additions': {'AccountIds': [self.a2_r1.config.account.account_id]}}
        try:
            self.a2_r1.oapi.UpdateSnapshot(SnapshotId=self.snap2_id, PermissionsToCreateVolume=permissions)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5054')
