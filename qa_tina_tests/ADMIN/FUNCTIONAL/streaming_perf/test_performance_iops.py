# -*- coding:utf-8 -*-
from __future__ import division

import re

import pytest

from qa_common_tools.ssh import SshTools

from qa_tina_tests.ADMIN.FUNCTIONAL.streaming import StreamingBase


@pytest.mark.region_admin
@pytest.mark.tag_qemu
class Test_performance_iops(StreamingBase):
    @classmethod
    def setup_class(cls):
        cls.w_size = 100
        cls.v_size = 1000
        cls.qemu_version = '2.12'
        cls.inst_type = 'm4.xlarge'
        cls.vol_type = 'io1'
        cls.iops = 1000
        cls.s_len = 10
        cls.branch = False
        cls.with_md5sum = False
        cls.with_fio = True
        super(Test_performance_iops, cls).setup_class()

    # def test_Txxxx_streaming(self):
    #    start_time = time.time()
    #    ret = self.a1_r1.intel.streaming.start(resource_id=self.vol_id_test, base_data_file=self.data['snap_2']['datafiles'][0])
    #    wait_streaming_state(self.a1_r1, self.vol_id_test, cleanup=True, sleep=5, max_it=150, logger=self.logger)
    #    elapsed_time = time.time() - start_time
    #    self.logger.info("streaming time: {}".format(elapsed_time))

    def run_perf(self, intermediate, read_only, fio_file, test_name):

        fio_time = 180

        if intermediate:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_id_test, base_data_file=self.data['snap_2']['datafiles'][0])
        else:
            self.a1_r1.intel.streaming.start(resource_id=self.vol_id_test)

        if read_only:
            mode = '--readonly --rw=randread'
        else:
            mode = '--rw=randwrite'
        cmd = (
            'sudo fio --filename={} --name test_fio --direct=1 {} --bs=16k --size=10G --numjobs=16 --time_based '
            '--runtime={} --group_reporting --norandommap'.format(fio_file, mode, fio_time)
        )
        out, _, _ = SshTools.exec_command_paramiko(self.test_sshclient, cmd, eof_time_out=fio_time + 30)
        self.logger.debug(out)
        match = re.search(': IOPS=([0-9-]+), ', out, re.MULTILINE)
        iops = match.group(1)
        self.logger.info(
            "IOPS: %s / %s / %s / Streaming: %s",
            test_name,
            "Intermediate" if intermediate else "Full",
            "ReadOnly" if read_only else "ReadWrite",
            iops,
        )
        key = "{}_and_{}".format("intermediate" if intermediate else "full", test_name)
        self.add_metric(key, iops)
        if int(iops) < self.iops:
            assert 100 * abs(self.iops - int(iops)) / self.iops < 60

        ret = self.a1_r1.intel.streaming.find_operations(volume=[self.vol_id_test])
        self.logger.debug(ret.response.display())
        assert ret.response.result[0].state == 'started'

    def test_T3284_perf_hot_vol_inter_snap_j_randwrite(self):
        self.run_perf(intermediate=True, read_only=False, fio_file='/vol/test_fio', test_name='randwrite')

    def test_T3285_perf_hot_vol_inter_snap_j_read_before_base_data_file(self):
        self.run_perf(intermediate=True, read_only=True, fio_file='/vol/fio_1', test_name='read_before_base_data_file')

    def test_T3286_perf_hot_vol_inter_snap_j_read_base_data_file(self):
        self.run_perf(intermediate=True, read_only=True, fio_file='/vol/fio_2', test_name='read_base_data_file')

    def test_T3287_perf_hot_vol_inter_snap_j_read_after_base_data_file(self):
        self.run_perf(intermediate=True, read_only=True, fio_file='/vol/fio_3', test_name='read_after_base_data_file')

    def test_T3288_perf_hot_vol_inter_snap_j_read_streamed_data_file(self):
        self.run_perf(intermediate=True, read_only=True, fio_file='/vol/fio_10', test_name='read_streamed_data_file')

    def test_T3289_perf_hot_vol_full_randwrite(self):
        self.run_perf(intermediate=False, read_only=False, fio_file='/vol/test_fio', test_name='randwrite')

    def test_T3290_perf_hot_vol_full_read_after_base_data_file(self):
        self.run_perf(intermediate=False, read_only=True, fio_file='/vol/fio_3', test_name='read_after_base_data_file')

    def test_T3291_perf_hot_vol_full_read_streamed_data_file(self):
        self.run_perf(intermediate=False, read_only=True, fio_file='/vol/fio_10', test_name='read_streamed_data_file')

    # Add test perf_snap_(inter|full)_...)
