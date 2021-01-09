# -*- coding:utf-8 -*-
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_tina_tests.USER.API.OAPI.Snapshot.Snapshot import Snapshot
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state


class Test_DeleteSnapshot(Snapshot):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteSnapshot, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteSnapshot, cls).teardown_class()

    def test_T2184_empty_param(self):
        try:
            self.a1_r1.oapi.DeleteSnapshot()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)

    def test_T2185_invalid_snapshot_id(self):
        try:
            self.a1_r1.oapi.DeleteSnapshot(SnapshotId='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104', None)

    def test_T2186_unknown_snapshot_id(self):
        try:
            self.a1_r1.oapi.DeleteSnapshot(SnapshotId='snap-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5054', None)

    def test_T2187_valid_case(self):
        snap_id = None
        try:
            snap_id = self.a1_r1.oapi.CreateSnapshot(VolumeId=self.volume_id1).response.Snapshot.SnapshotId
            wait_snapshots_state(self.a1_r1, [snap_id], state='completed')
            self.a1_r1.oapi.DeleteSnapshot(SnapshotId=snap_id)
            snap1_id = None
        finally:
            if snap1_id:
                self.a1_r1.oapi.DeleteSnapshot(SnapshotId=snap_id)

    @pytest.mark.tag_sec_confidentiality
    def test_T3517_with_other_user(self):
        snap_id = None
        try:
            snap_id = self.a1_r1.oapi.CreateSnapshot(VolumeId=self.volume_id1).response.Snapshot.SnapshotId
            wait_snapshots_state(self.a1_r1, [snap_id], state='completed')
            self.a2_r1.oapi.DeleteSnapshot(SnapshotId=snap_id)
            assert False, ('Call should not have been successful')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5054')
        finally:
            if snap_id:
                self.a1_r1.oapi.DeleteSnapshot(SnapshotId=snap_id)
