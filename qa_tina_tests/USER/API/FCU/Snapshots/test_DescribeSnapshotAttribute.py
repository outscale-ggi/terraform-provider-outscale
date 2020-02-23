# pylint: disable=missing-docstring

from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state, wait_volumes_state
from qa_common_tools.misc import assert_error

NB_SNAP = 1


class Test_DescribeSnapshotAttribute(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeSnapshotAttribute, cls).setup_class()
        cls.user1_acc_id = cls.a1_r1.config.account.account_id
        cls.user2_acc_id = cls.a2_r1.config.account.account_id
        region = cls.a1_r1.config.region.az_name
        cls.snap1_id = []
        cls.vol1_id = None
        try:
            cls.vol1_id = cls.a1_r1.fcu.CreateVolume(AvailabilityZone=region, VolumeType='standard', Size=5).response.volumeId
            wait_volumes_state(cls.a1_r1, [cls.vol1_id], state='available')
            for _ in range(NB_SNAP):
                snap_id = cls.a1_r1.fcu.CreateSnapshot(VolumeId=cls.vol1_id).response.snapshotId
                cls.snap1_id.append(snap_id)
                wait_snapshots_state(cls.a1_r1, [snap_id], state="completed")
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            cls.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=cls.snap1_id[0], CreateVolumePermission={'Remove' : [{'UserId': cls.user2_acc_id}]})
            if cls.snap1_id:
                cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=cls.snap1_id[0])
            if cls.vol1_id:
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.vol1_id)
        finally:
            super(Test_DescribeSnapshotAttribute, cls).teardown_class()

    def test_T3375_with_valid_account(self):
        try:
            self.a2_r1.fcu.DescribeSnapshotAttribute(SnapshotId=self.snap1_id[0], Attribute='createVolumePermission')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidSnapshot.NotFound",
                         "The Snapshot ID does not exist: " + self.snap1_id[0] + ", for account: " + self.user2_acc_id)
