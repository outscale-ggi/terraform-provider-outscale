# pylint: disable=missing-docstring

import random
import string

from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_volumes
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state, wait_snapshots_state


class Test_Attachement(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_Attachement, cls).setup_class()
        cls.inst_info = None
        cls.vol_id = None
        cls.loop = 50
        cls.nb_test = 0
        try:
            pass
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_Attachement, cls).teardown_class()

    def setup_method(self, method):
        super(Test_Attachement, self).setup_method(method)
        self.inst_info = None
        self.vol_id = None
        self.nb_test = 0
        try:
            self.inst_info = create_instances(self.a1_r1, state='running')
            _, [self.vol_id] = create_volumes(self.a1_r1, state='available')
        except Exception as error:
            try:
                self.teardown_method(method)
            finally:
                raise error

    def teardown_method(self, method):
        try:
            self.logger.info("stop after %d executions", self.nb_test)
            if self.vol_id:
                delete_volumes(self.a1_r1, [self.vol_id])
            if self.inst_info:
                delete_instances(self.a1_r1, self.inst_info)
        finally:
            super(Test_Attachement, self).teardown_method(method)

    def attach_detach(self, device, snap=False):
        self.nb_test += 1
        self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], VolumeId=self.vol_id, Device=device)
        ret = wait_volumes_state(self.a1_r1, [self.vol_id], state='in-use', nb_check=5)
        self.logger.debug(ret.response.display())
        if snap:
            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol_id).response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap_id])
            self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=[snap_id])
        self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_id)
        try:
            ret = wait_volumes_state(self.a1_r1, [self.vol_id], 'available', nb_check=5)
            self.logger.debug(ret.response.display())
        except AssertionError as error:
            self.logger.debug(error)
            self.logger.debug(str(error))
            if not snap:
                raise
            # retry ?
            self.logger.debug("retry detach...")
            self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_id)
            ret = wait_volumes_state(self.a1_r1, [self.vol_id], 'available', nb_check=5)
            self.logger.debug(ret.response.display())

    def test_T3690_multi_attach_detach_with_same_device_name(self):
        device = '/dev/xvdb'
        for _ in range(self.loop):
            self.attach_detach(device)

    def test_T3691_multi_attach_detach_with_snap_creation(self):
        device = '/dev/xvdb'
        for _ in range(self.loop):
            self.attach_detach(device, True)

    def test_T3692_multi_attach_detach_with_diff_device_name(self):
        for _ in range(self.loop):
            device = '/dev/xvd{}'.format(random.choice(string.ascii_lowercase[1:]))
            self.attach_detach(device)

    def test_T3693_multi_attach_detach_with_diff_device_name_and_snap_creation(self):
        for _ in range(self.loop):
            device = '/dev/xvd{}'.format(random.choice(string.ascii_lowercase[1:]))
            self.attach_detach(device, True)
