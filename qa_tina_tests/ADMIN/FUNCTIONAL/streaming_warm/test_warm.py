# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import pytest
from time import sleep

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.base import StreamingBase
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.utils import assert_streaming_state, wait_streaming_state, \
    get_streaming_operation, get_data_file_chain
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_volumes
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state, wait_volumes_state, wait_instances_state


def check_data_file_chain(osc_sdk, vol_id, vol_df_list):
    ret = get_data_file_chain(osc_sdk, vol_id)
    assert len(ret) == len(vol_df_list)
    for i in range(len(ret)):
        assert ret[i] == vol_df_list[i]


@pytest.mark.region_admin
@pytest.mark.tag_qemu
class Test_warm(StreamingBase):

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
        super(Test_warm, cls).setup_class()

    def setup_method(self, method):
        super(Test_warm, self).setup_method(method)
        try:
            self.attached = False
            self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_stopped_info[INSTANCE_ID_LIST][0], VolumeId=self.vol_1_id, Device='/dev/xvdc')
            wait_volumes_state(self.a1_r1, [self.vol_1_id], state='in-use')
            self.attached = True
        except:
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.attached:
                self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_1_id)
                try:
                    wait_volumes_state(self.a1_r1, [self.vol_1_id], state='available')
                except AssertionError:
                    self.logger.debug("Retry detach...")
                    self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_1_id)
                    wait_volumes_state(self.a1_r1, [self.vol_1_id], state='available')
        finally:
            super(Test_warm, self).teardown_method(method)

    def test_T3125_warm_vol_full(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_stream_full()
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_no_stream()

    def test_T4120_warm_vol_full_not_streamable(self):
        self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=False)
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-state - Volume is not allowed to stream (attr: streamable)')
        finally:
            self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=True)

    def test_T4121_warm_vol_full_and_detach(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_no_stream()
        self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_1_id)
        self.attached = False
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_stream_full()

    def test_T4122_warm_vol_full_and_start_inst(self):
        res_started = None
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
                self.a1_r1.fcu.StartInstances(InstanceId=[self.inst_stopped_info[INSTANCE_ID_LIST][0]])
                wait_instances_state(self.a1_r1, [self.inst_stopped_info[INSTANCE_ID_LIST][0]], state='running')
                res_started = True
                wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
                self.check_no_stream() # TODO: ???
            else:
                wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
                self.check_no_stream()

        finally:
            if res_started:
                self.a1_r1.fcu.StopInstances(InstanceId=[self.inst_stopped_info[INSTANCE_ID_LIST][0]])
                wait_instances_state(self.a1_r1, [self.inst_stopped_info[INSTANCE_ID_LIST][0]], state='stopped')

    def test_T4123_warm_vol_full_and_delete_snap(self):
        snap_id = self.vol_1_snap_list[-1]
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_no_stream()
        self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
        wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=snap_id)
        self.vol_1_snap_list.remove(snap_id)
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_stream_full()

    def test_T4124_warm_vol_full_and_snap_volume(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_no_stream()
        snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_1_id).response.snapshotId
        wait_snapshots_state(self.a1_r1, [snap_id], state='completed')
        self.vol_1_snap_list.append(snap_id)
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
            wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
            self.check_stream_full(nb_new_snap=1)
        #ret = get_data_file_chain(self.a1_r1, self.vol_1_id)
        #assert len(ret) == 4
        #assert ret[1] == self.vol_1_df_list[0]
        #assert ret[2] == self.vol_1_df_list[1]
        #assert ret[3] == self.vol_1_df_list[-1]

    def test_T4125_warm_vol_full_and_create_vol_from_snap_and_attach_stopped_inst(self):
        vol_id = None
        snap_id = self.vol_1_snap_list[-1]
        res_attach = False
        try:
            _, [vol_id] = create_volumes(self.a1_r1, snapshot_id=snap_id, size=self.v_size, volume_type=self.vol_type, iops=self.iops)
            wait_volumes_state(self.a1_r1, [vol_id], state='available')
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
            else:
                wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
                self.check_no_stream()
            self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_stopped_info[INSTANCE_ID_LIST][0], VolumeId=vol_id, Device='/dev/xvdr')
            wait_volumes_state(self.a1_r1, [self.vol_1_id], state='in-use')
            res_attach = True
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
                wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
                self.check_stream_full()
        finally:
            if res_attach:
                self.a1_r1.fcu.DetachVolume(VolumeId=vol_id)
                wait_volumes_state(self.a1_r1, [vol_id], state='available')
            if vol_id:
                delete_volumes(self.a1_r1, [vol_id])


    def test_T4126_warm_vol_full_and_create_vol_from_snap_and_attach_running_inst(self):
        vol_id = None
        snap_id = self.vol_1_snap_list[-1]
        res_attach = False
        try:
            _, [vol_id] = create_volumes(self.a1_r1, snapshot_id=snap_id, size=self.v_size, volume_type=self.vol_type, iops=self.iops)
            wait_volumes_state(self.a1_r1, [vol_id], state='available')
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
            else:
                wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
                self.check_no_stream()
            self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_running_info[INSTANCE_ID_LIST][0], VolumeId=vol_id, Device='/dev/xvdn')
            wait_volumes_state(self.a1_r1, [self.vol_1_id], state='in-use')
            res_attach = True
            if self.rebase_enabled:
                sleep(3)
                ret = get_streaming_operation(self.a1_r1, self.vol_1_id, self.logger)
                assert not ret.response.result
                check_data_file_chain(self.a1_r1, self.vol_1_id, self.vol_1_df_list) # ==> TODO update fucntion
        finally:
            if res_attach:
                self.a1_r1.fcu.DetachVolume(VolumeId=vol_id)
                wait_volumes_state(self.a1_r1, [vol_id], state='available')
            if vol_id:
                delete_volumes(self.a1_r1, [vol_id])

    def test_T4127_warm_snap_full(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
            wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
            self.check_stream_full()
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
            self.check_no_stream()


    def test_T4128_warm_snap_full_not_streamable(self):
        self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=False)
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-state - Volume is not allowed to stream (attr: streamable)')
        finally:
            self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=True)

    def test_T4129_warm_snap_full_and_detach(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
            self.check_no_stream()
        self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_1_id)
        self.attached = False
        wait_volumes_state(self.a1_r1, [self.vol_1_id], state='available')
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
            wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
            self.check_stream_full()

    def test_T4130_warm_snap_full_and_start_inst(self):
        res_started = None
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
                self.a1_r1.fcu.StartInstances(InstanceId=[self.inst_stopped_info[INSTANCE_ID_LIST][0]])
                wait_instances_state(self.a1_r1, [self.inst_stopped_info[INSTANCE_ID_LIST][0]], state='running')
                res_started = True
                wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
                self.check_no_stream() # TODO ???
            else:
                wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
                self.check_no_stream()
        finally:
            if res_started:
                self.a1_r1.fcu.StopInstances(InstanceId=[self.inst_stopped_info[INSTANCE_ID_LIST][0]])
                wait_instances_state(self.a1_r1, [self.inst_stopped_info[INSTANCE_ID_LIST][0]], state='stopped')

    def test_T4131_warm_snap_full_and_delete_snap(self):
        stream_snap_id = self.vol_1_snap_list[-1]
        self.a1_r1.intel.streaming.start(resource_id=stream_snap_id)
        if self.rebase_enabled:
            assert_streaming_state(self.a1_r1, stream_snap_id, 'started', self.logger)
        else:
            wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
            self.check_no_stream()
        self.a1_r1.fcu.DeleteSnapshot(SnapshotId=self.vol_1_snap_list[0])
        tmp_snap_id = self.vol_1_snap_list[0]
        self.vol_1_snap_list.remove(tmp_snap_id)
        wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=[tmp_snap_id])
        wait_streaming_state(self.a1_r1, stream_snap_id, cleanup=True, logger=self.logger)

    def test_T4132_warm_snap_full_and_snap_volume(self):
        snap_id = None
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
            else:
                wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
                self.check_no_stream()
            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_1_id).response.snapshotId
            wait_snapshots_state(self.a1_r1, [snap_id], state='completed')
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
                wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
                self.check_stream_full(nb_new_snap=1)
            #ret = get_data_file_chain(self.a1_r1, self.vol_1_id)
            #assert len(ret) == 4
            #assert ret[1] == self.vol_1_df_list[0]
            #assert ret[2] == self.vol_1_df_list[1]
            #assert ret[3] == self.vol_1_df_list[-1]
        finally:
            if snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)

    def test_T4133_warm_snap_full_and_create_vol_from_snap_and_attach_stopped_inst(self):
        vol_id = None
        snap_id = self.ref_snap_id
        res_attach = False
        try:
            _, [vol_id] = create_volumes(self.a1_r1, snapshot_id=snap_id, size=self.v_size, volume_type=self.vol_type, iops=self.iops)
            wait_volumes_state(self.a1_r1, [vol_id], state='available')
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
                self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_stopped_info[INSTANCE_ID_LIST][0], VolumeId=vol_id, Device='/dev/xvdj')
                wait_volumes_state(self.a1_r1, [self.vol_1_id], state='in-use')
                res_attach = True
                assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
                wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True)
                self.check_full_streaming()
            else:
                wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
                self.check_no_stream()
        finally:
            if res_attach :
                self.a1_r1.fcu.DetachVolume(VolumeId=vol_id)
                wait_volumes_state(self.a1_r1, [vol_id], state='available')
            if vol_id:
                delete_volumes(self.a1_r1, [vol_id])

    def test_T4134_warm_snap_full_and_create_vol_from_snap_and_attach_running_inst(self):
        vol_id = None
        snap_id = self.ref_snap_id
        res_attach = False
        try:
            _, [vol_id] = create_volumes(self.a1_r1, snapshot_id=snap_id, size=self.v_size, volume_type=self.vol_type, iops=self.iops)
            wait_volumes_state(self.a1_r1, [vol_id], state='available')
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
                self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_running_info[INSTANCE_ID_LIST][0], VolumeId=vol_id, Device='/dev/xvdn')
                wait_volumes_state(self.a1_r1, [self.vol_1_id], state='in-use')
                res_attach = True
                sleep(3)
                ret = get_streaming_operation(self.a1_r1, self.vol_1_id, self.logger)
                assert not ret.response.result
                check_data_file_chain(self.a1_r1, self.vol_1_id, self.vol_1_df_list)
            else:
                wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
                self.check_no_stream()
        finally:
            if res_attach :
                self.a1_r1.fcu.DetachVolume(VolumeId=vol_id)
                wait_volumes_state(self.a1_r1, [vol_id], state='available')
            if vol_id:
                delete_volumes(self.a1_r1, [vol_id])
