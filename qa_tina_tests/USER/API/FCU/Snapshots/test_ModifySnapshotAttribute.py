from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state
from qa_tina_tools.tools.tina.delete_tools import delete_volumes
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_test_tools.misc import assert_error, id_generator
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
import string
import pytest
from qa_tina_tools.constants import TWO_REGIONS_NEEDED


class Test_ModifySnapshotAttribute(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.snap_id = None
        cls.vol_id = None
        super(Test_ModifySnapshotAttribute, cls).setup_class()
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
        finally:
            super(Test_ModifySnapshotAttribute, cls).teardown_class()

    def teardown_method(self, method):
        try:
            if self.snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=self.snap_id)
                self.snap_id = None
        finally:
            OscTestSuite.teardown_method(self, method)

    def check_snapshot_res(self, res, volume_id, description, owner):
        assert res.snapshotId.startswith('snap-')
        assert len(res.snapshotId) == 13
        assert res.description == description
        assert res.ownerId == owner
        assert res.progress.endswith('%')
        assert float(res.progress[:-1]) >= 0 and float(res.progress[:-1]) <= 100
        assert res.startTime is not None
        assert res.status in ['in-queue', 'pending', 'completed']
        assert res.volumeId == volume_id
        assert res.volumeSize == '10'

    def test_T4172_with_invalid_len_snapshot_id(self):
        snp_id = id_generator(prefix="snap-", size=15, chars=string.hexdigits)
        try:
            self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=snp_id,
                                                   CreateVolumePermission={'Add': [{'UserId': self.a2_r1.config.account.account_id}]})
        except OscApiException as error:
            assert_error(error, 400, "InvalidSnapshotID.Malformed", "Invalid ID received: {}".format(snp_id))

    def test_T1060_with_valid_params(self):
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_id = res.snapshotId
        wait_snapshots_state(self.a1_r1, [self.snap_id], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description', self.a1_r1.config.account.account_id)
        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=self.snap_id,
                                               CreateVolumePermission={'Add': [{'UserId': self.a2_r1.config.account.account_id}]})

    def test_T1061_add_permission_for_current_user(self):
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_id = res.snapshotId
        wait_snapshots_state(self.a1_r1, [self.snap_id], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description', self.a1_r1.config.account.account_id)
        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=self.snap_id,
                                               CreateVolumePermission={'Add': [{'UserId': self.a1_r1.config.account.account_id}]})

    def test_T1062_with_invalid_user_id(self):
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_id = res.snapshotId
        wait_snapshots_state(self.a1_r1, [self.snap_id], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description', self.a1_r1.config.account.account_id)
        try:
            self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=self.snap_id, CreateVolumePermission={'Add': [{'UserId': "xxxxxxxxx"}]})
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidAMIAttributeItemValue", "Invalid attribute item value 'xxxxxxxxx' for userId item type.")

    def test_T1063_with_user_id_from_another_region(self):
        if not hasattr(self, 'a2_r2'):
            pytest.skip(TWO_REGIONS_NEEDED)
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_id = res.snapshotId
        wait_snapshots_state(self.a1_r1, [self.snap_id], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description', self.a1_r1.config.account.account_id)
        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=self.snap_id,
                                               CreateVolumePermission={'Add': [{'UserId': self.a2_r2.config.account.account_id}]})

    def test_T1064_with_unexisting_snapshot_id(self):
        snp_id = (id_generator(prefix="snap-99999", size=3, chars=string.hexdigits)).lower()
        try:
            self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=snp_id,
                                                   CreateVolumePermission={'Add': [{'UserId': self.a2_r1.config.account.account_id}]})
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidSnapshot.NotFound",
                         "The Snapshot ID does not exist: {}, for account: {}".format(snp_id, self.a1_r1.config.account.account_id))

    def test_T1065_with_invalid_snapshot_id(self):
        snp_id = id_generator(prefix="a", size=10, chars=string.hexdigits)
        try:
            self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=snp_id,
                                                   CreateVolumePermission={'Add': [{'UserId': self.a2_r1.config.account.account_id}]})
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidSnapshotID.Malformed",
                         "Invalid ID received: {}. Expected format: snap-".format(snp_id, self.a1_r1.config.account.account_id))

    @pytest.mark.tag_sec_confidentiality
    def test_T1066_with_snapshot_from_another_account(self):
        vol_id_user_2 = None
        snap_id_user2 = None
        try:
            _, [vol_id_user_2] = create_volumes(self.a2_r1, state='available')
            res = self.a2_r1.fcu.CreateSnapshot(VolumeId=vol_id_user_2, Description="description").response
            snap_id_user2 = res.snapshotId
            wait_snapshots_state(self.a2_r1, [snap_id_user2], state='completed')
            self.check_snapshot_res(res, vol_id_user_2, 'description', self.a2_r1.config.account.account_id)
            self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=snap_id_user2,
                                                   CreateVolumePermission={'Add': [{'UserId': self.a3_r1.config.account.account_id}]})
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidSnapshot.NotFound",
                         "The Snapshot ID does not exist: {}, for account: {}".format(snap_id_user2, self.a1_r1.config.account.account_id))
        finally:
            if vol_id_user_2:
                delete_volumes(self.a2_r1, [vol_id_user_2])
            if snap_id_user2:
                self.a2_r1.fcu.DeleteSnapshot(SnapshotId=snap_id_user2)

    def test_T1067_remove_permission_of_authorized_user(self):
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_id = res.snapshotId
        wait_snapshots_state(self.a1_r1, [self.snap_id], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description', self.a1_r1.config.account.account_id)
        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=self.snap_id,
                                               CreateVolumePermission={'Add': [{'UserId': self.a2_r1.config.account.account_id}]})
        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=self.snap_id,
                                               CreateVolumePermission={'Remove': [{'UserId': self.a2_r1.config.account.account_id}]})

    def test_T1068_remove_permission_with_invalid_user_id(self):
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_id = res.snapshotId
        wait_snapshots_state(self.a1_r1, [self.snap_id], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description', self.a1_r1.config.account.account_id)
        try:
            self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=self.snap_id,
                                                   CreateVolumePermission={'Remove': [{'UserId': "xxxxxxxxx"}]})
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidAMIAttributeItemValue", "Invalid attribute item value 'xxxxxxxxx' for userId item type.")

    def test_T1069_remove_permission_with_user_id_from_another_region(self):
        if not hasattr(self, 'a2_r2'):
            pytest.skip(TWO_REGIONS_NEEDED)
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_id = res.snapshotId
        wait_snapshots_state(self.a1_r1, [self.snap_id], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description', self.a1_r1.config.account.account_id)
        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=self.snap_id,
                                               CreateVolumePermission={'Remove': [{'UserId': self.a2_r2.config.account.account_id}]})

    def test_T1070_remove_permission_with_unauthorized_user_id(self):
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_id = res.snapshotId
        wait_snapshots_state(self.a1_r1, [self.snap_id], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description', self.a1_r1.config.account.account_id)
        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=self.snap_id,
                                               CreateVolumePermission={'Add': [{'UserId': self.a2_r1.config.account.account_id}]})
        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=self.snap_id,
                                               CreateVolumePermission={'Remove': [{'UserId': self.a3_r1.config.account.account_id}]})

    def test_T1071_remove_permission_without_attribute(self):
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_id = res.snapshotId
        wait_snapshots_state(self.a1_r1, [self.snap_id], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description', self.a1_r1.config.account.account_id)
        try:
            self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=self.snap_id, CreateVolumePermission='')
            assert False, "Call shouldn't successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterType', "Value of parameter 'CreateVolumePermission' must be of type: dict. Received: ")

    def test_T1072_remove_permission_with_invalid_attribute(self):
        res = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id, Description="description").response
        self.snap_id = res.snapshotId
        wait_snapshots_state(self.a1_r1, [self.snap_id], state='completed')
        self.check_snapshot_res(res, self.vol_id, 'description', self.a1_r1.config.account.account_id)
        try:
            self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=self.snap_id, CreateVolumePermission={'Invalid attribute': ""})
            assert False, "Call shouldn't successful"
        except OscApiException as error:
            assert_error(error, 400, "OWS.Error", "Request is not valid.")

    def test_T1073_remove_permission_with_unexisting_snapshot_id(self):
        snap_id = (id_generator(prefix="snap-999", size=5, chars=string.hexdigits)).lower()
        try:
            self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=snap_id,
                                                   CreateVolumePermission={'Remove': [{'UserId': self.a2_r1.config.account.account_id}]})
            assert False, "Call shouldn't successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidSnapshot.NotFound",
                         "The Snapshot ID does not exist: {}, for account: {}".format(snap_id, self.a1_r1.config.account.account_id))

    def test_T1074_remove_permission_with_invalid_snapshot_id(self):
        snap_id = (id_generator(prefix="sna", size=10, chars=string.hexdigits)).lower()
        try:
            self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=snap_id,
                                                   CreateVolumePermission={'Remove': [{'UserId': self.a2_r1.config.account.account_id}]})
            assert False, "Call shouldn't successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidSnapshotID.Malformed", "Invalid ID received: {}. Expected format: snap-".format(snap_id))

    @pytest.mark.tag_sec_confidentiality
    def test_T1075_remove_permission_with_snapshot_id_from_another_account(self):
        try:
            _, [vol_id] = create_volumes(self.a2_r1, state='available')
            res = self.a2_r1.fcu.CreateSnapshot(VolumeId=vol_id, Description="description").response
            snap_id = res.snapshotId
            wait_snapshots_state(self.a2_r1, [snap_id], state='completed')
            self.check_snapshot_res(res, vol_id, 'description', self.a2_r1.config.account.account_id)
            self.a2_r1.fcu.ModifySnapshotAttribute(SnapshotId=snap_id,
                                                   CreateVolumePermission={'Add': [{'UserId': self.a3_r1.config.account.account_id}]})
            self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=snap_id,
                                                   CreateVolumePermission={'Remove': [{'UserId': self.a3_r1.config.account.account_id}]})
            assert False, "Call shouldn't successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshot.NotFound',
                         "The Snapshot ID does not exist: {}, for account: {}".format(snap_id, self.a1_r1.config.account.account_id))
        finally:
            delete_volumes(self.a2_r1, [vol_id])
            self.a2_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
