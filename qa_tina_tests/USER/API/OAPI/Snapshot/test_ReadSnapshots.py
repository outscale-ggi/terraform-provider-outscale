# -*- coding:utf-8 -*-
import pytest
from qa_tina_tests.USER.API.OAPI.Snapshot.Snapshot import Snapshot
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state
from osc_common.exceptions.osc_exceptions import OscApiException


class Test_ReadSnapshots(Snapshot):

    @classmethod
    def setup_class(cls):
        super(Test_ReadSnapshots, cls).setup_class()
        cls.snap1_id = None
        cls.known_error = False
        try:
            cls.snap1_id = cls.a1_r1.oapi.CreateSnapshot(VolumeId=cls.volume_id1).response.Snapshot.SnapshotId
            cls.snap2_id = cls.a1_r1.oapi.CreateSnapshot(VolumeId=cls.volume_id2, Description='1..2..3').response.Snapshot.SnapshotId
            cls.snap3_id = cls.a1_r1.oapi.CreateSnapshot(VolumeId=cls.volume_id1, Description='4..5..6').response.Snapshot.SnapshotId
            wait_snapshots_state(cls.a1_r1, [cls.snap1_id, cls.snap2_id, cls.snap3_id], state='completed')
            permissions = {'Additions': {'AccountIds': [cls.a2_r1.config.account.account_id]}}
            cls.a1_r1.oapi.UpdateSnapshot(SnapshotId=cls.snap2_id, PermissionsToCreateVolume=permissions)
            permissions = {'Additions': {'GlobalPermission': True}}
            cls.a1_r1.oapi.UpdateSnapshot(SnapshotId=cls.snap3_id, PermissionsToCreateVolume=permissions)
        except Exception:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.snap1_id:
                cls.a1_r1.oapi.DeleteSnapshot(SnapshotId=cls.snap1_id)
                wait_snapshots_state(cls.a1_r1, [cls.snap1_id], cleanup=True)
                cls.snap1_id = None
            if cls.snap2_id:
                cls.a1_r1.oapi.DeleteSnapshot(SnapshotId=cls.snap2_id)
                wait_snapshots_state(cls.a1_r1, [cls.snap2_id], cleanup=True)
                cls.snap2_id = None
            if cls.snap3_id:
                cls.a1_r1.oapi.DeleteSnapshot(SnapshotId=cls.snap3_id)
                wait_snapshots_state(cls.a1_r1, [cls.snap3_id], cleanup=True)
                cls.snap3_id = None
        finally:
            super(Test_ReadSnapshots, cls).teardown_class()

    def test_T2188_empty_filters(self):
        ret = self.a1_r1.oapi.ReadSnapshots().response.Snapshots
        assert len(ret) >= 3
        for snap in ret:
            self.validate_snasphot(snap)

    def test_T2189_filters_account_ids(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'AccountIds': [self.a1_r1.config.account.account_id]}).response.Snapshots
        assert len(ret) == 3
        for snap in ret:
            self.validate_snasphot(snap, expected_snap={
                'AccountId': self.a1_r1.config.account.account_id,
            })
            assert snap.SnapshotId in [self.snap1_id, self.snap2_id, self.snap3_id]

    def test_T2190_filters_snap_id1(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'SnapshotIds': [self.snap1_id]}).response.Snapshots
        assert len(ret) == 1
        self.validate_snasphot(ret[0], expected_snap={
            'Description': '',
            'AccountId': self.a1_r1.config.account.account_id,
            'SnapshotId': self.snap1_id,
            'VolumeId': self.volume_id1,
            'VolumeSize': 2,
        })

    def test_T2191_filters_states_pending(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'States': ['pending/queued']}).response.Snapshots
        assert len(ret) >= 0
        for snap in ret:
            self.validate_snasphot(snap, expected_snap={
                'State': 'pending/queued',
                'Progress': 0,
            })

    def test_T2192_filters_states_completed(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'States': ['completed']}).response.Snapshots
        assert len(ret) >= 0
        for snap in ret:
            self.validate_snasphot(snap, expected_snap={
                'State': 'completed',
                'Progress': 100,
            })

    def test_T2193_filters_a1_permissions_account_a1(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'PermissionsToCreateVolumeAccountIds':
                                                     [self.a1_r1.config.account.account_id]}).response.Snapshots
        assert len(ret) == 0

    def test_T2194_filters_a1_permissions_account_a2(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'PermissionsToCreateVolumeAccountIds':
                                                     [self.a2_r1.config.account.account_id]}).response.Snapshots
        assert len(ret) == 1
        for snap in ret:
            self.validate_snasphot(snap, expected_snap={
                'SnapshotId': self.snap2_id,
            }, permission={'AccountIds': [self.a2_r1.config.account.account_id]})

    def test_T2195_filters_a2_permissions_account_a1(self):
        ret = self.a2_r1.oapi.ReadSnapshots(Filters={'PermissionsToCreateVolumeAccountIds':
                                                     [self.a1_r1.config.account.account_id]}).response.Snapshots
        assert len(ret) == 0

    def test_T2196_filters_a2_permissions_account_a2(self):
        ret = self.a2_r1.oapi.ReadSnapshots(Filters={'PermissionsToCreateVolumeAccountIds':
                                                     [self.a2_r1.config.account.account_id]}).response.Snapshots
        assert len(ret) == 1
        for snap in ret:
            self.validate_snasphot(snap, expected_snap={
                'SnapshotId': self.snap2_id,
            }, permission={'AccountIds': [self.a2_r1.config.account.account_id]})

    def test_T2197_filters_a1_permissions_global_permission_true(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'PermissionsToCreateVolumeGlobalPermission': True}).response.Snapshots
        assert len(ret) >= 1
        for snap in ret:
            self.validate_snasphot(snap, permission={'GlobalPermission': True})

    def test_T3082_filters_a1_permissions_global_permission_false(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'PermissionsToCreateVolumeGlobalPermission': False}).response.Snapshots
        for snap in ret:
            self.validate_snasphot(snap, permission={'GlobalPermission': False})

    @pytest.mark.tag_sec_confidentiality
    def test_T3434_with_other_account(self):
        ret = self.a3_r1.oapi.ReadSnapshots().response.Snapshots
        assert len(ret) == 1
        assert ret[0].SnapshotId == self.snap3_id

    @pytest.mark.tag_sec_confidentiality
    def test_T3435_with_other_account_filters(self):
        ret = self.a3_r1.oapi.ReadSnapshots(Filters={'AccountIds': [self.a2_r1.config.account.account_id]}).response.Snapshots
        assert len(ret) == 0

    def test_T3533_filters_descriptions(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'Descriptions': ['1..2..3']}).response.Snapshots
        assert len(ret) == 1
        for snap in ret:
            self.validate_snasphot(snap, expected_snap={
                'SnapshotId': self.snap2_id,
                'Description': '1..2..3',
            })

    def test_T3534_filters_progresses_100(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'Progresses': [100]}).response.Snapshots
        for snap in ret:
            self.validate_snasphot(snap, expected_snap={
                'Progress': 100,
            })

    def test_T3535_filters_progresses_0(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'Progresses': [0]}).response.Snapshots
        for snap in ret:
            self.validate_snasphot(snap, expected_snap={
                'Progress': 0,
            })

    def test_T3536_filters_volume_ids(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'VolumeIds': [self.volume_id2]}).response.Snapshots
        for snap in ret:
            self.validate_snasphot(snap, expected_snap={
                'SnapshotId': self.snap2_id,
                'VolumeId': self.volume_id2,
            })

    def test_T3537_filters_volume_sizes(self):
        try:
            ret = self.a1_r1.oapi.ReadSnapshots(Filters={'VolumeSizes': [2]}).response.Snapshots
            for snap in ret:
                self.validate_snasphot(snap, expected_snap={
                    'VolumeSize': 2,
                })
        except OscApiException as error:
            raise error

    def test_T3811_filters_account_aliases(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'AccountAliases': ['toto']}).response.Snapshots
        assert len(ret) == 0
