# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_test_tools.misc import assert_error
from qa_tina_tools.tools.tina.delete_tools import delete_volumes
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state, wait_volumes_state

from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.base import StreamingBase
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.utils import assert_streaming_state, wait_streaming_state, get_data_file_chain


@pytest.mark.region_admin
@pytest.mark.tag_qemu
class Test_cold(StreamingBase):

    @classmethod
    def setup_class(cls):
        cls.w_size = 20
        cls.v_size = 10
        cls.qemu_version = '2.12'
        #cls.rebase_enabled = False
        cls.inst_type = 'c4.large'
        cls.vol_type = 'standard'
        cls.iops = None
        cls.base_snap_id = 10
        cls.new_snap_count = 1  # > 1
        cls.branch_id = None  # [0, new_snap_count-1]
        cls.fio = False
        cls.inst_running = True
        cls.inst_stopped = True
        cls.check_data = False # TODO: change...
        super(Test_cold, cls).setup_class()

    def setup_method(self, method):
        super(Test_cold, self).setup_method(method)
        try:
            pass
        except:
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            pass
        finally:
            super(Test_cold, self).teardown_method(method)

    def test_T3123_cold_vol_full(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_stream_full()
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_no_stream()

    #def test_T0000_cold_vol_inter(self):
    #    self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id, base_data_file=self.vol_1_df_list[4])
    #    assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
    #    wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
    #    self.check_intermediate_streaming()

    def test_T4103_cold_vol_full_not_streamable(self):
        self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=False)
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-state - Volume is not allowed to stream (attr: streamable)')
        finally:
            self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=True)

    def test_T4104_cold_vol_full_and_delete_vol(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_no_stream()
        wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger) # Cancelled
        delete_volumes(self.a1_r1, [self.vol_1_id])
        self.vol_1_id = None

    def test_T4105_cold_vol_full_and_delete_snap(self):
        snap_id = self.vol_1_snap_list[-1]
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
            self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=snap_id)
            self.vol_1_snap_list.remove(snap_id)
            assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_stream_full()
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_no_stream()
            self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=snap_id)
            self.vol_1_snap_list.remove(snap_id)

    def test_T4118_cold_vol_full_and_snap_volume(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_1_id).response.snapshotId
            wait_snapshots_state(self.a1_r1, [snap_id], state='completed')
            self.vol_1_snap_list.append(snap_id)
            assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_stream_full(nb_new_snap=1)
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_no_stream()
            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_1_id).response.snapshotId
            wait_snapshots_state(self.a1_r1, [snap_id], state='completed')
            self.vol_1_snap_list.append(snap_id)

    def test_T4106_cold_vol_full_and_attach_stopped_inst(self):
        attached = False
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
            else:
                wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
                self.check_no_stream()
            self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_stopped_info[INSTANCE_ID_LIST][0], VolumeId=self.vol_1_id, Device='/dev/xvdc')
            wait_volumes_state(self.a1_r1, [self.vol_1_id], state='in-use')
            attached = True
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
                wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
                self.check_stream_full()
        finally:
            if attached:
                self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_1_id)
                wait_volumes_state(self.a1_r1, [self.vol_1_id], state='available')

    def test_T4107_cold_vol_full_and_attach_running_inst(self):
        attached = False
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
            else:
                wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
                self.check_no_stream()
            self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_running_info[INSTANCE_ID_LIST][0], VolumeId=self.vol_1_id, Device='/dev/xvdc')
            wait_volumes_state(self.a1_r1, [self.vol_1_id], state='in-use')
            attached = True
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_id, 'interrupted', self.logger)
                # TODO: add start all and check streaming
        finally:
            if attached:
                self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_1_id)
                wait_volumes_state(self.a1_r1, [self.vol_1_id], state='available')

    #def test_T4108_cold_vol_full_and_create_vol_from_snap_and_attach_stopped_inst(self):
    #    pass

    #def test_T4109_cold_vol_full_and_create_vol_from_snap_and_attach_running_inst(self):
    #    pass

    def test_T4110_cold_snap_full(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
            wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
            self.check_stream_full()
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
            self.check_no_stream()

    def test_T4111_cold_snap_full_not_streamable(self):
        self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=False)
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-state - Volume is not allowed to stream (attr: streamable)')
        finally:
            self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=True)

    def test_T4112_cold_snap_full_and_delete_vol(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
            self.check_no_stream()
        delete_volumes(self.a1_r1, [self.vol_1_id])
        self.vol_1_id = None
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
            wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
            ret = get_data_file_chain(self.a1_r1, self.vol_1_snap_list[-1])
            assert len(ret) == 2
            assert ret[0] == self.vol_1_df_list[1]
            assert ret[1] == self.vol_1_df_list[-1]

    def test_T4113_cold_snap_full_and_delete_snap(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
            self.check_no_stream()
        self.a1_r1.fcu.DeleteSnapshot(SnapshotId=self.vol_1_snap_list[-1])
        wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=self.vol_1_snap_list[-1])
        wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger) # Cancelled
        self.vol_1_snap_list.remove(self.vol_1_snap_list[-1])

    def test_T4119_cold_snap_full_and_snap_volume(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_1_id).response.snapshotId
            wait_snapshots_state(self.a1_r1, [snap_id], state='completed')
            assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
            wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger) # --> cancelled
            self.check_stream_full(nb_new_snap=1)
            self.vol_1_snap_list.append(snap_id)
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
            self.check_no_stream()
            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_1_id).response.snapshotId
            wait_snapshots_state(self.a1_r1, [snap_id], state='completed')
            self.vol_1_snap_list.append(snap_id)

    def test_T4114_cold_snap_full_and_attach_stopped_inst(self):
        attached = False
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
            else:
                wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
                self.check_no_stream()
            self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_stopped_info[INSTANCE_ID_LIST][0], VolumeId=self.vol_1_id, Device='/dev/xvdc')
            wait_volumes_state(self.a1_r1, [self.vol_1_id], state='in-use')
            attached = True
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
                wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
                self.check_stream_full()
        finally:
            if attached:
                self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_1_id)
                wait_volumes_state(self.a1_r1, [self.vol_1_id], state='available')

    def test_T4115_cold_snap_full_and_attach_running_inst(self):
        attached = False
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
            else:
                wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
                self.check_no_stream()
            self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_running_info[INSTANCE_ID_LIST][0], VolumeId=self.vol_1_id, Device='/dev/xvdc')
            wait_volumes_state(self.a1_r1, [self.vol_1_id], state='in-use')
            attached = True
            if self.rebase_enabled:
                wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger) # --> cancelled
                ret = get_data_file_chain(self.a1_r1, self.vol_1_snap_list[-1])
                assert ret == self.vol_1_df_list[1:]
        finally:
            if attached:
                self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_1_id)
                wait_volumes_state(self.a1_r1, [self.vol_1_id], state='available')

    #def test_T4116_cold_snap_full_and_create_vol_from_snap_and_attach_stopped_inst(self):
    #    pass

    #def test_T4117_cold_snap_full_and_create_vol_from_snap_and_attach_running_inst(self):
    #    pass
