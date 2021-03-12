

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state

NB_SNAP = 1


class Test_DescribeSnapshots(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeSnapshots, cls).setup_class()
        cls.snap1_id = []  # snapshots ids for user1
        cls.vol1_id = None  # volumes ids for user1
        try:
            _, [cls.vol1_id] = create_volumes(cls.a1_r1, state="available")
            for _ in range(NB_SNAP):
                snap_id = cls.a1_r1.fcu.CreateSnapshot(VolumeId=cls.vol1_id).response.snapshotId
                cls.snap1_id.append(snap_id)
                wait_snapshots_state(cls.a1_r1, [snap_id], state="completed")
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.snap1_id:
                for snap_id in cls.snap1_id:
                    cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            if cls.vol1_id:
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.vol1_id)
        finally:
            super(Test_DescribeSnapshots, cls).teardown_class()

    def test_T3187_from_other_account(self):
        try:
            self.a2_r1.fcu.DescribeSnapshots(SnapshotId=self.snap1_id[0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshot.NotFound', "The snapshot '" + self.snap1_id[0] + "' does not exist.")

#    def test_TXXX_filter_restorable_by(self):
#        _, vol_id_list = create_volumes(osc_sdk=self.a1_r1, state='available')
#        snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=vol_id_list[0]).response.snapshotId
#        wait_snapshots_state(self.a1_r1, [snap_id], 'completed')
#        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=snap_id,
#                                               CreateVolumePermission={'Add': [{'UserId': self.a2_r1.config.account.account_id}]})
#        ret1 = self.a1_r1.fcu.DescribeSnapshots(RestorableBy=[self.a1_r1.config.account.account_id])
#        ret2 = self.a1_r1.fcu.DescribeSnapshots(RestorableBy=[self.a2_r1.config.account.account_id])
#        ret3 = self.a2_r1.fcu.DescribeSnapshots(RestorableBy=[self.a1_r1.config.account.account_id])
#        ret4 = self.a2_r1.fcu.DescribeSnapshots(RestorableBy=[self.a2_r1.config.account.account_id])
#        print('toto')
