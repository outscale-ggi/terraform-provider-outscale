from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_volumes
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state


class Snapshot(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.volume_id1 = None
        cls.volume_id2 = None
        super(Snapshot, cls).setup_class()
        try:
            _, [cls.volume_id1] = create_volumes(cls.a1_r1, size=2)
            _, [cls.volume_id2] = create_volumes(cls.a1_r1, size=4)
            wait_volumes_state(cls.a1_r1, [cls.volume_id1, cls.volume_id2], state='available')
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.volume_id1:
                delete_volumes(cls.a1_r1, [cls.volume_id1])
                cls.volume_id1 = None
            if cls.volume_id2:
                delete_volumes(cls.a1_r1, [cls.volume_id2])
                cls.volume_id2 = None
        finally:
            super(Snapshot, cls).teardown_class()

    def validate_snasphot(self, snap, **kwargs):
        """
        :param snap:
        :param kwargs:
            expected_snap
            permission
        :return:
        """
        expected_snap = kwargs.get('expected_snap', {})
        for k, v in expected_snap.items():
            assert getattr(snap, k) == v, (
                'In Snapshot, {} is different of expected value {} for key {}'
                .format(getattr(snap, k), v, k))
        assert snap.SnapshotId.startswith('snap-')
        assert snap.State in ['completed', 'pending', 'pending/queued']
        assert isinstance(snap.Progress, int)
        assert 0 <= snap.Progress <= 100
        permission = kwargs.get('permission')
        if permission:
            if hasattr(permission, 'AccountIds'):
                assert len(permission.AccountIds) == len(snap.PermissionsToCreateVolume.AccountIds[0])
                assert snap.PermissionsToCreateVolume.AccountIds[0] in permission.AccountIds
            if hasattr(permission, 'GlobalPermission'):
                assert snap.PermissionsToCreateVolume.GlobalPermission == permission.GlobalPermission
        else:
            assert hasattr(snap, 'PermissionsToCreateVolume')
