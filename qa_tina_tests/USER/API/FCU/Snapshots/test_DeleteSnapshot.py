from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.state import SnapshotStatus, VolumeStatus
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state, wait_volumes_state


class Test_DeleteSnapshot(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vol1_id = None
        super(Test_DeleteSnapshot, cls).setup_class()
        try:
            # create volumes
            _, vol_id_list = create_volumes(cls.a1_r1)
            wait_volumes_state(cls.a1_r1, vol_id_list, VolumeStatus.Available.value)
            cls.vol1_id = vol_id_list[0]
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vol1_id:
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.vol1_id)
        finally:
            super(Test_DeleteSnapshot, cls).teardown_class()

    def test_T1030_with_valid_param(self):
        snap_id = None
        try:
            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol1_id).response.snapshotId
            wait_snapshots_state(self.a1_r1, [snap_id], SnapshotStatus.Completed.value)
            self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            snap_id = None
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)

    def test_T1701_with_missing_id(self):
        try:
            self.a1_r1.fcu.DeleteSnapshot()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Insufficient parameters provided out of: Force, snapshotIDs. Expected at least: 1')
            known_error('TINA-5095', 'Wrong error message')
            assert_error(error, 400, '', '')

    def test_T1032_with_unknown_id(self):
        try:
            self.a1_r1.fcu.DeleteSnapshot(SnapshotId='snap-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshot.NotFound',
                         "The Snapshot ID does not exist: snap-12345678, for account: {}".format(self.a1_r1.config.account.account_id))

    def test_T1031_with_invalid_id(self):
        try:
            self.a1_r1.fcu.DeleteSnapshot(SnapshotId='xxx-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshotID.Malformed', "Invalid ID received: xxx-12345678. Expected format: snap-")

    def test_T1033_from_another_account(self):
        snap_id = None
        try:
            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol1_id).response.snapshotId
            wait_snapshots_state(self.a1_r1, [snap_id], SnapshotStatus.Completed.value)
            self.a2_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            snap_id = None
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshot.NotFound',
                         "The Snapshot ID does not exist: {}, for account: {}".format(snap_id, self.a2_r1.config.account.account_id))
        finally:
            if snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
