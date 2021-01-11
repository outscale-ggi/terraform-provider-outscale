# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import time

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.base import StreamingBase
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.utils import assert_streaming_state, wait_streaming_state, get_streaming_operation
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state, wait_volumes_state, wait_instances_state


class StreamingBaseHot(StreamingBase):

    def setup_method(self, method):
        super(StreamingBaseHot, self).setup_method(method)
        try:
            self.attached = False
            self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_running_info[INSTANCE_ID_LIST][0], VolumeId=self.vol_1_id, Device='/dev/xvdc')
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
                    wait_volumes_state(self.a1_r1, [self.vol_1_id], 'available')
        finally:
            super(StreamingBaseHot, self).teardown_method(method)

    def detach(self, resource_id):
        assert_streaming_state(self.a1_r1, resource_id, 'started', self.logger)
        time.sleep(2)
        self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_1_id)
        wait_volumes_state(self.a1_r1, [self.vol_1_id], 'available')
        self.attached = False
        if self.rebase_enabled:
            ret = get_streaming_operation(osc_sdk=self.a1_r1, res_id=resource_id, logger=self.logger)
            if ret.response.result[0].state == 'interrupted':
                ret = self.a1_r1.intel.streaming.start_all() # TODO Remove and add known error
                self.logger.debug(ret.response.display())
                wait_streaming_state(self.a1_r1, resource_id, state='started', logger=self.logger)
            assert_streaming_state(self.a1_r1, resource_id, 'started', self.logger)
            wait_streaming_state(self.a1_r1, resource_id, cleanup=True, logger=self.logger)
        else:
            assert_streaming_state(self.a1_r1, resource_id, 'interrupted', self.logger)

    def stop(self, resource_id):
        running = True
        try:
            assert_streaming_state(self.a1_r1, resource_id, 'started', self.logger)
            time.sleep(2)
            self.a1_r1.fcu.StopInstances(InstanceId=self.inst_running_info[INSTANCE_ID_LIST])
            wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=self.inst_running_info[INSTANCE_ID_LIST], state='stopped')
            running = False
            #if resource_id.startswith('vol-'):
            assert_streaming_state(self.a1_r1, resource_id, 'interrupted', self.logger)
            try:
                ret = self.a1_r1.intel.streaming.start_all()
                self.logger.debug(ret.response.display())
            except OscApiException as err:
                if err.status_code == 504:
                    self.logger.debug("streaming.start_all TIMEOUT...")
                    time.sleep(30)
                else:
                    raise err
            if self.rebase_enabled:
                assert_streaming_state(self.a1_r1, resource_id, 'started', self.logger)
                wait_streaming_state(self.a1_r1, resource_id, cleanup=True, logger=self.logger)
            else:
                assert_streaming_state(self.a1_r1, resource_id, 'interrupted', self.logger)
        finally:
            if not running:
                self.a1_r1.fcu.StartInstances(InstanceId=self.inst_running_info[INSTANCE_ID_LIST])
                wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=self.inst_running_info[INSTANCE_ID_LIST], state='running')
                if not self.rebase_enabled:
                    try:
                        ret = self.a1_r1.intel.streaming.start_all()
                        self.logger.debug(ret.response.display())
                    except OscApiException as err:
                        if err.status_code == 504:
                            self.logger.debug("streaming.start_all TIMEOUT...")
                            time.sleep(60)
                        else:
                            raise err
                    if resource_id.startswith('vol-'):
                        assert_streaming_state(self.a1_r1, resource_id, 'started', self.logger)
                        wait_streaming_state(self.a1_r1, resource_id, cleanup=True, logger=self.logger)

    def snapshot(self, resource_id):
        snap_id = None
        try:
            assert_streaming_state(self.a1_r1, resource_id, 'started', self.logger)
            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_1_id).response.snapshotId
            assert_streaming_state(self.a1_r1, resource_id, 'started', self.logger)
            wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap_id])
            wait_streaming_state(self.a1_r1, resource_id, cleanup=True, logger=self.logger)
        finally:
            if snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
                wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=[snap_id])

    def reboot(self, resource_id):
        assert_streaming_state(self.a1_r1, resource_id, 'started', self.logger)
        self.a1_r1.fcu.RebootInstances(InstanceId=self.inst_running_info[INSTANCE_ID_LIST])
        time.sleep(5)
        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=self.inst_running_info[INSTANCE_ID_LIST], state='ready')
        ret = get_streaming_operation(osc_sdk=self.a1_r1, res_id=resource_id, logger=self.logger)
        if ret.response.result and ret.response.result[0].state == 'interrupted':
            wait_streaming_state(self.a1_r1, resource_id, 'started', logger=self.logger)
        wait_streaming_state(self.a1_r1, resource_id, cleanup=True, logger=self.logger)

    def delete_snap(self, resource_id, snap_id):
        assert_streaming_state(self.a1_r1, resource_id, 'started', self.logger)
        self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
        wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=[snap_id])
        self.vol_1_snap_list.remove(snap_id)
        #assert_streaming_state(self.a1_r1, resource_id, 'started', self.logger)
        wait_streaming_state(self.a1_r1, resource_id, cleanup=True, logger=self.logger)

