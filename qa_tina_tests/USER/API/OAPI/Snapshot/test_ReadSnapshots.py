
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state
from qa_tina_tests.USER.API.OAPI.Snapshot.Snapshot import Snapshot, validate_snasphot


class Test_ReadSnapshots(Snapshot):

    @classmethod
    def setup_class(cls):
        super(Test_ReadSnapshots, cls).setup_class()
        cls.snap_ids = []
        cls.known_error = False
        try:
            cls.snap_ids.append(cls.a1_r1.oapi.CreateSnapshot(VolumeId=cls.volume_id1).response.Snapshot.SnapshotId)
            cls.snap_ids.append(cls.a1_r1.oapi.CreateSnapshot(VolumeId=cls.volume_id2, Description='1..2..3').response.Snapshot.SnapshotId)
            cls.snap_ids.append(cls.a1_r1.oapi.CreateSnapshot(VolumeId=cls.volume_id1, Description='4..5..6').response.Snapshot.SnapshotId)
            cls.snap_ids.append(cls.a1_r1.oapi.CreateSnapshot(VolumeId=cls.volume_id1, Description='7..8..9').response.Snapshot.SnapshotId)
            wait_snapshots_state(cls.a1_r1, cls.snap_ids, state='completed')
            permissions = {'Additions': {'AccountIds': [cls.a2_r1.config.account.account_id]}}
            cls.a1_r1.oapi.UpdateSnapshot(SnapshotId=cls.snap_ids[1], PermissionsToCreateVolume=permissions)
            permissions = {'Additions': {'GlobalPermission': True}}
            cls.a1_r1.oapi.UpdateSnapshot(SnapshotId=cls.snap_ids[2], PermissionsToCreateVolume=permissions)
        except Exception:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            for snap_id in cls.snap_ids:
                cls.a1_r1.oapi.DeleteSnapshot(SnapshotId=snap_id)
            wait_snapshots_state(cls.a1_r1, cls.snap_ids, cleanup=True)
        finally:
            super(Test_ReadSnapshots, cls).teardown_class()

    def test_T2188_empty_filters(self):
        ret = self.a1_r1.oapi.ReadSnapshots().response.Snapshots
        assert len(ret) >= 3
        for snap in ret:
            validate_snasphot(snap)

    def test_T2189_filters_account_ids(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'AccountIds': [self.a1_r1.config.account.account_id]}).response.Snapshots
        assert len(ret) == 4
        for snap in ret:
            validate_snasphot(snap, expected_snap={
                'AccountId': self.a1_r1.config.account.account_id,
            })
            assert snap.SnapshotId in self.snap_ids

    def test_T2190_filters_snap_id1(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'SnapshotIds': [self.snap_ids[0]]}).response.Snapshots
        assert len(ret) == 1
        validate_snasphot(ret[0], expected_snap={
            'Description': '',
            'AccountId': self.a1_r1.config.account.account_id,
            'SnapshotId': self.snap_ids[0],
            'VolumeId': self.volume_id1,
            'VolumeSize': 2,
        })

    def test_T2191_filters_states_pending(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'States': ['pending/queued']}).response.Snapshots
        assert len(ret) >= 0
        for snap in ret:
            validate_snasphot(snap, expected_snap={
                'State': 'pending/queued',
                'Progress': 0,
            })

    def test_T2192_filters_states_completed(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'States': ['completed']}).response.Snapshots
        assert len(ret) >= 0
        for snap in ret:
            validate_snasphot(snap, expected_snap={
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
            validate_snasphot(snap, expected_snap={
                'SnapshotId': self.snap_ids[1],
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
            validate_snasphot(snap, expected_snap={
                'SnapshotId': self.snap_ids[1],
            }, permission={'AccountIds': [self.a2_r1.config.account.account_id]})

    def test_T2197_filters_a1_permissions_global_permission_true(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'PermissionsToCreateVolumeGlobalPermission': True}).response.Snapshots
        assert len(ret) >= 1
        for snap in ret:
            validate_snasphot(snap, permission={'GlobalPermission': True})

    def test_T3082_filters_a1_permissions_global_permission_false(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'PermissionsToCreateVolumeGlobalPermission': False}).response.Snapshots
        for snap in ret:
            validate_snasphot(snap, permission={'GlobalPermission': False})

    @pytest.mark.tag_sec_confidentiality
    def test_T3434_with_other_account(self):
        ret = self.a3_r1.oapi.ReadSnapshots().response.Snapshots
        assert len(ret) == 1
        assert ret[0].SnapshotId == self.snap_ids[2]

    @pytest.mark.tag_sec_confidentiality
    def test_T3435_with_other_account_filters(self):
        ret = self.a3_r1.oapi.ReadSnapshots(Filters={'AccountIds': [self.a2_r1.config.account.account_id]}).response.Snapshots
        assert len(ret) == 0

    def test_T3533_filters_descriptions(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'Descriptions': ['1..2..3']}).response.Snapshots
        assert len(ret) == 1
        for snap in ret:
            validate_snasphot(snap, expected_snap={
                'SnapshotId': self.snap_ids[1],
                'Description': '1..2..3',
            })

    def test_T3534_filters_progresses_100(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'Progresses': [100]}).response.Snapshots
        for snap in ret:
            validate_snasphot(snap, expected_snap={
                'Progress': 100,
            })

    def test_T3535_filters_progresses_0(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'Progresses': [0]}).response.Snapshots
        for snap in ret:
            validate_snasphot(snap, expected_snap={
                'Progress': 0,
            })

    def test_T3536_filters_volume_ids(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'VolumeIds': [self.volume_id2]}).response.Snapshots
        for snap in ret:
            validate_snasphot(snap, expected_snap={
                'SnapshotId': self.snap_ids[1],
                'VolumeId': self.volume_id2,
            })

    def test_T3537_filters_volume_sizes(self):
        try:
            ret = self.a1_r1.oapi.ReadSnapshots(Filters={'VolumeSizes': [2]}).response.Snapshots
            for snap in ret:
                validate_snasphot(snap, expected_snap={
                    'VolumeSize': 2,
                })
        except OscApiException as error:
            raise error

    def test_T3811_filters_account_aliases(self):
        ret = self.a1_r1.oapi.ReadSnapshots(Filters={'AccountAliases': ['toto']}).response.Snapshots
        assert len(ret) == 0

    def test_T5979_with_tag_filter(self):
        indexes, _ = misc.execute_tag_tests(self.a1_r1, 'Snapshot', self.snap_ids,
                                            'oapi.ReadSnapshots', 'Snapshots.SnapshotId')
        assert indexes == [5, 6, 7, 8, 9, 10, 24, 25, 26, 27, 28, 29]
        known_error('API-399', 'ReadSnapshots does not support wildcards filtering')
