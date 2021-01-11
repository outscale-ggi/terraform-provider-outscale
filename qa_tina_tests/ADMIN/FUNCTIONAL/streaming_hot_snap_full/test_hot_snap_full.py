# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import pytest
import time

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.utils import wait_streaming_state, assert_streaming_state
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming_hot.base import StreamingBaseHot


@pytest.mark.region_admin
@pytest.mark.tag_qemu
class Test_hot_snap_full(StreamingBaseHot):

    @classmethod
    def setup_class(cls):
        cls.w_size = 20
        cls.v_size = 10
        cls.qemu_version = '2.12'
        cls.inst_type = 'c4.xlarge'
        cls.vol_type = 'standard'
        cls.iops = None
        cls.base_snap_id = 40
        cls.new_snap_count = 1  # > 1
        cls.branch_id = None  # [0, new_snap_count-1]
        cls.fio = False
        cls.inst_running = True
        cls.inst_stopped = False
        cls.check_data = True
        super(Test_hot_snap_full, cls).setup_class()

    def test_T3097_hot_snap_full(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
        assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
        wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
        self.check_stream_full()

    def test_T4136_hot_snap_full_not_streamable(self):
        self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=False)
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-state - Volume is not allowed to stream (attr: streamable)')
        finally:
            self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=True)

    def test_T3152_hot_snap_full_and_detach(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
        self.detach(resource_id=self.vol_1_snap_list[-1])
        if self.rebase_enabled:
            self.check_stream_full()
        else:
            self.check_no_stream()

    def test_T3153_hot_snap_full_and_stop(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
        self.stop(resource_id=self.vol_1_snap_list[-1])
        if self.rebase_enabled:
            self.check_stream_full()
        else:
            self.check_no_stream()

    def test_T3150_hot_snap_full_and_snapshot(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
        self.snapshot(resource_id=self.vol_1_snap_list[-1])
        self.check_stream_full(nb_new_snap=1)

    def test_T3154_hot_snap_full_and_reboot(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
        self.reboot(resource_id=self.vol_1_snap_list[-1])
        self.check_stream_full()

    def test_T4216_hot_snap_full_and_delete_snap(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
        self.delete_snap(resource_id=self.vol_1_snap_list[-1], snap_id=self.vol_1_snap_list[-1])
        self.check_no_stream()
        time.sleep(60) # Why ?
        #self.vol_1_snap_list.remove(self.vol_1_snap_list[-1])

    def test_T4217_hot_snap_full_and_stream_twice(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
        assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
            assert False
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-state - Streaming already started')
        assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
        wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
        self.check_stream_full()
