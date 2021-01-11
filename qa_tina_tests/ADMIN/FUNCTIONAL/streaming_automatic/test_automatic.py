# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import pytest

from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.utils import wait_streaming_state, assert_streaming_state
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming_hot.base import StreamingBaseHot


@pytest.mark.region_admin
class Test_automatic(StreamingBaseHot):

    @classmethod
    def setup_class(cls):
        cls.w_size = 20
        cls.v_size = 10
        cls.qemu_version = '2.12'
        #cls.rebase_enabled = False
        cls.inst_type = 'c4.xlarge'
        cls.vol_type = 'standard'
        cls.iops = None
        cls.base_snap_id = 45
        cls.new_snap_count = 10  # > 1
        cls.branch_id = None  # [0, new_snap_count-1]
        cls.fio = False
        cls.inst_running = True
        cls.inst_stopped = False
        cls.check_data = True
        super(Test_automatic, cls).setup_class()


    def test_T3328_hot_vol_full_auto_auto(self):
        self.a1_r1.intel.streaming.start_all()
        assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
        wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
        self.check_stream_full()

    def test_T3947_hot_vol_full_auto_not_streamable_vol(self):
        self.a1_r1.intel.volume.update(owner=self.a1_r1.config.account.account_id, volume=self.vol_1_id, streamable=False)
        self.a1_r1.intel.streaming.start_all()
        wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
        self.check_no_stream()
