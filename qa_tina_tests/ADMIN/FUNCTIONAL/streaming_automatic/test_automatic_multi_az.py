# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import pytest

from qa_tina_tests.ADMIN.FUNCTIONAL.streaming_hot.base import StreamingBaseHot
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.utils import wait_streaming_state, assert_streaming_state

@pytest.mark.region_admin
class Test_automatic_multi_az(StreamingBaseHot):

    @classmethod
    def setup_class(cls):
        cls.w_size = 20
        cls.v_size = 10
        cls.qemu_version = '2.12'
        #cls.rebase_enabled = False
        cls.inst_type = 'tinav1.c2r4p1'
        cls.inst_az = 'b'
        cls.vol_type = 'standard'
        cls.iops = None
        cls.base_snap_id = 10
        cls.new_snap_count = 10  # > 1
        cls.branch_id = None  # [0, new_snap_count-1]
        cls.fio = False
        cls.inst_running = True
        cls.inst_stopped = False
        cls.check_data = True
        super(Test_automatic_multi_az, cls).setup_class()


    def test_T5089_hot_vol_full_auto_multi_az(self):
        resp = self.a1_r1.intel.streaming.find_inter_az_volumes().response
        for i in resp.result:
            if i.resource_id == self.vol_1_id:
                return
        assert False, "Volume bnot found"
        #self.a1_r1.intel.streaming.start_all()
        #assert_streaming_state(self.a1_r1, self.vol_1_id, 'started', self.logger)
        #wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True, logger=self.logger)
        #self.check_stream_full()
