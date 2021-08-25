import pytest

from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.utils import assert_streaming_state, wait_streaming_state
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming_hot.base import StreamingBaseHot


@pytest.mark.region_admin
@pytest.mark.tag_qemu
class Test_hot_2_3(StreamingBaseHot):
    @classmethod
    def setup_class(cls):
        cls.w_size = 20
        cls.v_size = 10
        cls.qemu_version = '2.3'
        # cls.rebase_enabled = False
        cls.inst_type = 'tinav4.c2r4p2'
        cls.vol_type = 'standard'
        cls.iops = None
        cls.base_snap_id = 10
        cls.new_snap_count = 1  # > 1
        cls.branch_id = None  # [0, new_snap_count-1]
        cls.fio = False
        cls.inst_running = True
        cls.inst_stopped = False
        cls.check_data = True
        super(Test_hot_2_3, cls).setup_class()

    def test_T5882_hot_vol_full_2_3(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
        wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
        self.check_stream_full()

    def test_T5883_hot_snap_full_2_3(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1])
        assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
        wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
        self.check_stream_full()

    def test_T5884_hot_vol_inter_2_3(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id, base_data_file=self.vol_1_df_list[self.base_snap_id])
        assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
        wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
        self.check_stream_inter()

    def test_T5885_hot_snap_inter_2_3(self):
        self.a1_r1.intel.streaming.start(resource_id=self.vol_1_snap_list[-1], base_data_file=self.vol_1_df_list[self.base_snap_id])
        assert_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], 'started', self.logger)
        wait_streaming_state(self.a1_r1, self.vol_1_snap_list[-1], cleanup=True, logger=self.logger)
        self.check_stream_inter()
