from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_volumes
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state, wait_volumes_state


class Test_get_related_volumes(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_get_related_volumes, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_get_related_volumes, cls).teardown_class()

    def test_T2278_from_another_account(self):
        vol_id_list = None
        snap_id = None
        user1_vol_id_list = None
        user2_vol_id_list = None
        try:
            _, vol_id_list = create_volumes(self.a1_r1)
            wait_volumes_state(self.a1_r1, vol_id_list, state='available')
            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=vol_id_list[0]).response.snapshotId
            wait_snapshots_state(self.a1_r1, [snap_id], state='completed')
            self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=snap_id,
                                                   CreateVolumePermission={'Add': [{'UserId': self.a2_r1.config.account.account_id}]})

            _, user1_vol_id_list = create_volumes(self.a1_r1, count=2, snapshot_id=snap_id, state='available')
            _, user2_vol_id_list = create_volumes(self.a2_r1, count=2, snapshot_id=snap_id, state='available')
            wait_volumes_state(self.a1_r1, user1_vol_id_list, state='available')
            wait_volumes_state(self.a2_r1, user2_vol_id_list, state='available')

            ret = self.a1_r1.intel.snapshot.get_related_volumes(snapshot_id=snap_id)
            assert len(ret.response.result) == 4
            related_vol_ids = [res.id for res in ret.response.result]
            for vol_id in user1_vol_id_list:
                assert vol_id in related_vol_ids
            for vol_id in user2_vol_id_list:
                assert vol_id in related_vol_ids
        finally:
            if user1_vol_id_list:
                delete_volumes(self.a1_r1, user1_vol_id_list)
            if user2_vol_id_list:
                delete_volumes(self.a2_r1, user2_vol_id_list)
            if snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            if vol_id_list:
                delete_volumes(self.a1_r1, vol_id_list)
