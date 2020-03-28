from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state
from qa_tina_tools.tools.tina.delete_tools import delete_volumes
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import assert_error, id_generator
import string
from time import sleep
import pytest
from qa_tina_tools.constants import TWO_REGIONS_NEEDED


class Test_CopySnapshot(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.snap_ids = []
        cls.snap_copies_ids = []
        cls.snap_copies_ids_u2 = []
        cls.vol_id = None
        super(Test_CopySnapshot, cls).setup_class()
        try:
            _, [cls.vol_id] = create_volumes(cls.a1_r1, state='available')
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vol_id:
                delete_volumes(cls.a1_r1, [cls.vol_id])
            if cls.snap_copies_ids:
                for snap_cp_id in cls.snap_copies_ids:
                    cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_cp_id)
            if cls.snap_ids:
                for snap_id in cls.snap_ids:
                    cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            sleep(10)
            if cls.snap_copies_ids_u2:
                for snap_id_u2 in cls.snap_copies_ids_u2:
                    cls.a2_r1.fcu.DeleteSnapshot(SnapshotId=snap_id_u2)
        finally:
            super(Test_CopySnapshot, cls).teardown_class()

    def check_snapshot_res(self, res, volume_id, description):
        assert res.snapshotId.startswith('snap-')
        assert len(res.snapshotId) == 13
        assert res.description == description
        assert res.ownerId == self.a1_r1.config.account.account_id or res.ownerId == self.a2_r1.config.account.account_id
        assert res.progress.endswith('%')
        assert float(res.progress[:-1]) >= 0 and float(res.progress[:-1]) <= 100
        assert res.startTime is not None
        assert res.status in ['in-queue', 'pending', 'completed']
        assert res.volumeId == volume_id
        assert res.volumeSize == '10'

    def test_T4161_valid_params(self):
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_ids.append(res.snapshotId)
        wait_snapshots_state(self.a1_r1, [res.snapshotId], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description')
        res2 = self.a1_r1.fcu.CopySnapshot(SourceSnapshotId=res.snapshotId, SourceRegion=self.a1_r1.config.region_name)
        wait_snapshots_state(self.a1_r1, [res2.response.snapshotId], state='completed')
        self.snap_copies_ids.append(res2.response.snapshotId)

    def test_T1009_invalid_snapshot_id(self):
        snapshotId = id_generator(prefix="inv-", size=10, chars=string.hexdigits)
        try:
            res = self.a1_r1.fcu.CopySnapshot(SourceSnapshotId=snapshotId, SourceRegion=self.a1_r1.config.region_name)
            wait_snapshots_state(self.a1_r1, [res.response.snapshotId], state='completed')
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterValue",
                         "Value ({}) for parameter sourceSnapshotId is invalid. Expected: 'snap-...'.".format(snapshotId))

    def test_T1010_unexisting_snapshot_id(self):
        snapshotId = id_generator(prefix="snap-9", size=7, chars=(string.hexdigits).lower())
        try:
            res = self.a1_r1.fcu.CopySnapshot(SourceSnapshotId=snapshotId, SourceRegion=self.a1_r1.config.region_name)
            wait_snapshots_state(self.a1_r1, [res.response.snapshotId], state='completed')
            assert False, "Call shouldn't successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidSnapshot.NotFound",
                         "The Snapshot ID does not exist: {}, for account: {}".format(snapshotId, self.a1_r1.config.account.account_id))

    def test_T1007_from_another_account(self):
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_ids.append(res.snapshotId)
        wait_snapshots_state(self.a1_r1, [res.snapshotId], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description')
        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=res.snapshotId,
                                               CreateVolumePermission={'Add': [{'UserId': self.a2_r1.config.account.account_id}]})
        res2 = self.a2_r1.fcu.CopySnapshot(SourceSnapshotId=res.snapshotId, SourceRegion=self.a1_r1.config.region_name)
        wait_snapshots_state(self.a2_r1, [res2.response.snapshotId], state='completed')
        self.snap_copies_ids_u2.append(res2.response.snapshotId)

    def test_T1011_unauthorized_snapshot_id(self):
        if not hasattr(self, 'a1_r2'):
            pytest.skip(TWO_REGIONS_NEEDED)
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_ids.append(res.snapshotId)
        wait_snapshots_state(self.a1_r1, [res.snapshotId], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description')
        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=res.snapshotId,
                                               CreateVolumePermission={'Add': [{'UserId': self.a3_r1.config.account.account_id}]})
        try:
            res2 = self.a2_r1.fcu.CopySnapshot(SourceSnapshotId=res.snapshotId, SourceRegion=self.a1_r2.config.region_name).response
            wait_snapshots_state(self.a1_r1, [res2.snapshotId], state='completed')
            self.snap_copies_ids_u2.append(res2.snapshotId)
            assert False, "Call shouldn't successful"
        except OscApiException as error:
            assert_error(error, 400,
                         "InvalidSnapshot.NotFound",
                         "The Snapshot ID does not exist: {}, for account: {}".format(res.snapshotId, self.a2_r1.config.account.account_id))

    def test_T1012_unauthorized_region(self):
        if not hasattr(self, 'a1_r2'):
            pytest.skip(TWO_REGIONS_NEEDED)
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_ids.append(res.snapshotId)
        wait_snapshots_state(self.a1_r1, [res.snapshotId], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description')
        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=res.snapshotId,
                                               CreateVolumePermission={'Add': [{'UserId': self.a2_r1.config.account.account_id}]})
        try:
            # res_quota = self.a3_r1.icu.ReadQuotas(QuotaNames=["snapshot_copy_limit"])
            res2 = self.a2_r1.fcu.CopySnapshot(SourceSnapshotId=res.snapshotId, SourceRegion=self.a1_r2.config.region_name)
            wait_snapshots_state(self.a1_r1, [res2.snapshotId], state='completed')
            self.snap_copies_ids_u2.append(res2.response.snapshotId)
            assert False, "Call shouldn't successful"
        except OscApiException as error:
            assert_error(error, 400, "NotImplemented", "Inter-region copy is not implemented")

    def test_T1013_invalid_region(self):
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_ids.append(res.snapshotId)
        wait_snapshots_state(self.a1_r1, [res.snapshotId], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description')
        wait_snapshots_state(self.a1_r1, [res.snapshotId], state='completed')
        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=res.snapshotId,
                                               CreateVolumePermission={'Add': [{'UserId': self.a2_r1.config.account.account_id}]})
        try:
            res2 = self.a2_r1.fcu.CopySnapshot(SourceSnapshotId=res.snapshotId, SourceRegion="Invalid_Region")
            self.snap_copies_ids_u2.append(res2.response.snapshotId)
            assert False, "Call shouldn't successful"
        except OscApiException as error:
            assert_error(error, 400, "NotImplemented", "Inter-region copy is not implemented")
