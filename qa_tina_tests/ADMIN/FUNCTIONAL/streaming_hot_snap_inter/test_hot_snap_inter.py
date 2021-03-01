# -*- coding:utf-8 -*-
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error

from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.utils import assert_streaming_state, wait_streaming_state
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming_hot.base import StreamingBaseHot


@pytest.mark.region_admin
@pytest.mark.tag_qemu
class Test_hot_snap_inter(StreamingBaseHot):
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
        cls.branch_id = 0  # [0, new_snap_count-1]
        cls.fio = False
        cls.inst_running = True
        cls.inst_stopped = False
        cls.check_data = True
        super(Test_hot_snap_inter, cls).setup_class()

    def test_T3110_hot_snap_inter(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1], base_data_file=self.vol_1_df_list[self.base_snap_id])
        assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
        wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
        self.check_stream_inter()

    def test_T4220_hot_snap_inter_not_streamable(self):
        self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=False)
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1], base_data_file=self.vol_1_df_list[self.base_snap_id])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-state - Volume is not allowed to stream (attr: streamable)')
        finally:
            self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=True)

    def test_T3297_hot_snap_inter_and_detach(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1], base_data_file=self.vol_1_df_list[self.base_snap_id])
        self.detach(resource_id=self.vol_1_snap_list[-1])
        if self.rebase_enabled:
            # self.check_stream_inter()
            self.check_stream_full(mode="COLD")  # ==> TODO: Open Jira and add known error !!!
        else:
            self.check_no_stream()

    def test_T3298_hot_snap_inter_and_stop(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1], base_data_file=self.vol_1_df_list[self.base_snap_id])
        self.stop(resource_id=self.vol_1_snap_list[-1])
        if self.rebase_enabled:
            self.check_stream_inter()
        else:
            self.check_no_stream()

    def test_T3296_hot_snap_inter_and_snapshot(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1], base_data_file=self.vol_1_df_list[self.base_snap_id])
        self.snapshot(resource_id=self.vol_1_snap_list[-1])
        self.check_stream_inter(nb_new_snap=1)

    def test_T3299_hot_snap_inter_and_reboot(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1], base_data_file=self.vol_1_df_list[self.base_snap_id])
        self.reboot(resource_id=self.vol_1_snap_list[-1])
        # self.check_stream_inter()
        self.check_stream_full()  # ==> TODO: Open Jira and add known error !!!

    def test_T4221_hot_snap_inter_and_delete_snap(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1], base_data_file=self.vol_1_df_list[self.base_snap_id])
        self.delete_snap(resource_id=self.vol_1_snap_list[-1], snap_id=self.vol_1_snap_list[-1])
        # self.vol_1_snap_list.remove(self.vol_1_snap_list[-1])
        self.check_no_stream()
        # self.check_stream_inter() # ==> TODO: ???

    def test_T4222_hot_snap_inter_and_stream_twice(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1], base_data_file=self.vol_1_df_list[self.base_snap_id])
        assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
        try:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1], base_data_file=self.vol_1_df_list[self.base_snap_id])
            # assert False # ==> TODO: Open Jira and add known error !!!
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-state - Streaming already started')
        assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
        wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
        self.check_stream_inter()
