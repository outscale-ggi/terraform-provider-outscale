# pylint: disable=missing-docstring
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.constants import CODE_INJECT
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances, delete_volumes
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state, wait_volumes_state, wait_snapshots_state


class Test_CreateSnapshot(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.snap_ids = []
        cls.std_unattached_vol_id = None
        cls.std_stopped_attached_vol_id = None
        cls.std_running_attached_vol_id = None
        cls.unattached_vol_id = None
        cls.stopped_attached_vol_id = None
        cls.running_attached_vol_id = None
        cls.unattached_vol_id = None
        cls.stopped_attached_vol_id = None
        cls.running_attached_vol_id = None
        cls.other_account_vol_id = None
        cls.inst_info = None
        cls.stopped_vm_id = None
        cls.running_vm_id = None
        cls.std_attach_stopped = None
        cls.std_attach_running = None
        cls.io1_attach_stopped = None
        cls.io1_attach_running = None
        cls.gp2_attach_stopped = None
        cls.gp2_attach_running = None
        super(Test_CreateSnapshot, cls).setup_class()
        # create unattached volume
        # create volume attached on stopped vm
        # create volume attached on running vm
        try:
            cls.inst_info = create_instances(cls.a1_r1, nb=2, state=None)
            cls.stopped_vm_id = cls.inst_info[INSTANCE_ID_LIST][0]
            cls.running_vm_id = cls.inst_info[INSTANCE_ID_LIST][1]
            _, [cls.std_unattached_vol_id, cls.std_stopped_attached_vol_id, cls.std_running_attached_vol_id] = \
                create_volumes(cls.a1_r1, count=3, state='available', volume_type='standard')
            _, [cls.io1_unattached_vol_id, cls.io1_stopped_attached_vol_id, cls.io1_running_attached_vol_id] = \
                create_volumes(cls.a1_r1, count=3, state='available', volume_type='io1', iops=200)
            _, [cls.gp2_unattached_vol_id, cls.gp2_stopped_attached_vol_id, cls.gp2_running_attached_vol_id] = \
                create_volumes(cls.a1_r1, count=3, state='available', volume_type='gp2')
            _, [cls.other_account_vol_id] = create_volumes(cls.a2_r1, count=1, state='available')
            wait_instances_state(cls.a1_r1, [cls.stopped_vm_id, cls.running_vm_id], state='running')
            stop_instances(cls.a1_r1, [cls.stopped_vm_id])
            cls.std_attach_stopped = cls.a1_r1.fcu.AttachVolume(VolumeId=cls.std_stopped_attached_vol_id,
                                                                InstanceId=cls.stopped_vm_id, Device='/dev/xvdb')
            cls.std_attach_running = cls.a1_r1.fcu.AttachVolume(VolumeId=cls.std_running_attached_vol_id,
                                                                InstanceId=cls.running_vm_id, Device='/dev/xvdb')
            cls.io1_attach_stopped = cls.a1_r1.fcu.AttachVolume(VolumeId=cls.io1_stopped_attached_vol_id,
                                                                InstanceId=cls.stopped_vm_id, Device='/dev/xvdc')
            cls.io1_attach_running = cls.a1_r1.fcu.AttachVolume(VolumeId=cls.io1_running_attached_vol_id,
                                                                InstanceId=cls.running_vm_id, Device='/dev/xvdc')
            cls.gp2_attach_stopped = cls.a1_r1.fcu.AttachVolume(VolumeId=cls.gp2_stopped_attached_vol_id,
                                                                InstanceId=cls.stopped_vm_id, Device='/dev/xvdd')
            cls.gp2_attach_running = cls.a1_r1.fcu.AttachVolume(VolumeId=cls.gp2_running_attached_vol_id,
                                                                InstanceId=cls.running_vm_id, Device='/dev/xvdd')
            wait_volumes_state(cls.a1_r1, [cls.std_stopped_attached_vol_id, cls.std_running_attached_vol_id], state='in-use')
            wait_volumes_state(cls.a1_r1, [cls.io1_stopped_attached_vol_id, cls.io1_running_attached_vol_id], state='in-use')
            wait_volumes_state(cls.a1_r1, [cls.gp2_stopped_attached_vol_id, cls.gp2_running_attached_vol_id], state='in-use')
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.std_attach_stopped:
                cls.a1_r1.fcu.DetachVolume(VolumeId=cls.std_stopped_attached_vol_id, InstanceId=cls.stopped_vm_id)
            if cls.std_attach_running:
                cls.a1_r1.fcu.DetachVolume(VolumeId=cls.std_running_attached_vol_id, InstanceId=cls.running_vm_id)
            delete_volumes(cls.a1_r1, [cls.std_unattached_vol_id, cls.std_stopped_attached_vol_id, cls.std_running_attached_vol_id])
            if cls.io1_attach_stopped:
                cls.a1_r1.fcu.DetachVolume(VolumeId=cls.io1_stopped_attached_vol_id, InstanceId=cls.stopped_vm_id)
            if cls.io1_attach_running:
                cls.a1_r1.fcu.DetachVolume(VolumeId=cls.io1_running_attached_vol_id, InstanceId=cls.running_vm_id)
            delete_volumes(cls.a1_r1, [cls.io1_unattached_vol_id, cls.io1_stopped_attached_vol_id, cls.io1_running_attached_vol_id])
            if cls.gp2_attach_stopped:
                cls.a1_r1.fcu.DetachVolume(VolumeId=cls.gp2_stopped_attached_vol_id, InstanceId=cls.stopped_vm_id)
            if cls.gp2_attach_running:
                cls.a1_r1.fcu.DetachVolume(VolumeId=cls.gp2_running_attached_vol_id, InstanceId=cls.running_vm_id)
            delete_volumes(cls.a1_r1, [cls.gp2_unattached_vol_id, cls.gp2_stopped_attached_vol_id, cls.gp2_running_attached_vol_id])
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_CreateSnapshot, cls).teardown_class()

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        self.snap_ids = []

    def teardown_method(self, method):
        try:
            if self.snap_ids:
                for snap_id in self.snap_ids:
                    self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T3051_empty_param(self):
        try:
            self.a1_r1.fcu.CreateSnapshot()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: VolumeID')
            known_error('TINA-4790', 'Incorrect error message')
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: VolumeId')

    def test_T1018_invalid_volume_id(self):
        try:
            self.a1_r1.fcu.CreateSnapshot(VolumeId='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVolumeID.Malformed', 'Invalid ID received: tata. Expected format: vol-')

    def test_T1016_unknown_volume_id(self):
        try:
            self.a1_r1.fcu.CreateSnapshot(VolumeId='vol-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVolume.NotFound', "The volume 'vol-12345678' does not exist.")

    @pytest.mark.tag_sec_confidentiality
    def test_T1017_other_account_volume_id(self):
        try:
            self.a1_r1.fcu.CreateSnapshot(VolumeId=self.other_account_vol_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVolume.NotFound', "The volume '{}' does not exist.".format(self.other_account_vol_id))

    @pytest.mark.tag_sec_injection
    def test_T3814_code_injection_in_description(self):
        for desc in CODE_INJECT:
            ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.std_unattached_vol_id, Description=desc).response
            self.logger.debug(ret.display())
            self.snap_ids.append(ret.snapshotId)
            wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')
            self.check_snapshot_ret(ret, self.std_unattached_vol_id, desc)

    def check_snapshot_ret(self, ret, volume_id, description):
        assert ret.snapshotId.startswith('snap-')
        assert len(ret.snapshotId) == 13
        assert ret.description == description
        assert ret.ownerId == self.a1_r1.config.account.account_id
        assert ret.progress.endswith('%')
        assert float(ret.progress[:-1]) >= 0 and float(ret.progress[:-1]) <= 100
        assert ret.startTime is not None
        assert ret.status in ['in-queue', 'pending', 'completed']
        assert ret.volumeId == volume_id
        assert ret.volumeSize == '10'

    def test_T3052_std_unattached_vol(self):
        ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.std_unattached_vol_id, Description="description").response
        self.snap_ids.append(ret.snapshotId)
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')
        self.check_snapshot_ret(ret, self.std_unattached_vol_id, 'description')
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')

    def test_T3053_std_stopped_attached_vol(self):
        ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.std_stopped_attached_vol_id, Description="description").response
        self.snap_ids.append(ret.snapshotId)
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')
        self.check_snapshot_ret(ret, self.std_stopped_attached_vol_id, 'description')
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')

    def test_T3054_std_running_attached_vol(self):
        ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.std_running_attached_vol_id, Description="description").response
        self.snap_ids.append(ret.snapshotId)
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')
        self.check_snapshot_ret(ret, self.std_running_attached_vol_id, 'description')
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')

    def test_T3055_io1_unattached_vol(self):
        ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.io1_unattached_vol_id, Description="description").response
        self.snap_ids.append(ret.snapshotId)
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')
        self.check_snapshot_ret(ret, self.io1_unattached_vol_id, 'description')
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')

    def test_T3056_io1_stopped_attached_vol(self):
        ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.io1_stopped_attached_vol_id, Description="description").response
        self.snap_ids.append(ret.snapshotId)
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')
        self.check_snapshot_ret(ret, self.io1_stopped_attached_vol_id, 'description')
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')

    def test_T3057_io1_running_attached_vol(self):
        ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.io1_running_attached_vol_id, Description="description").response
        self.snap_ids.append(ret.snapshotId)
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')
        self.check_snapshot_ret(ret, self.io1_running_attached_vol_id, 'description')
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')

    def test_T3058_gp2_unattached_vol(self):
        ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.gp2_unattached_vol_id, Description="description").response
        self.snap_ids.append(ret.snapshotId)
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')
        self.check_snapshot_ret(ret, self.gp2_unattached_vol_id, 'description')
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')

    def test_T3059_gp2_stopped_attached_vol(self):
        ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.gp2_stopped_attached_vol_id, Description="description").response
        self.snap_ids.append(ret.snapshotId)
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')
        self.check_snapshot_ret(ret, self.gp2_stopped_attached_vol_id, 'description')
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')

    def test_T3060_gp2_running_attached_vol(self):
        ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.gp2_running_attached_vol_id, Description="description").response
        self.snap_ids.append(ret.snapshotId)
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')
        self.check_snapshot_ret(ret, self.gp2_running_attached_vol_id, 'description')
        wait_snapshots_state(self.a1_r1, [ret.snapshotId], state='completed')

    def multi_snapshot(self, volume_id, wait=True):
        ret1 = self.a1_r1.fcu.CreateSnapshot(VolumeId=volume_id, Description="description").response
        self.snap_ids.append(ret1.snapshotId)
        if wait:
            wait_snapshots_state(self.a1_r1, [ret1.snapshotId], state='completed')
        ret2 = self.a1_r1.fcu.CreateSnapshot(VolumeId=volume_id, Description="description").response
        self.snap_ids.append(ret2.snapshotId)
        wait_snapshots_state(self.a1_r1, [ret1.snapshotId, ret2.snapshotId], state='completed')

    def test_T3061_std_multi_slow_unattached_vol(self):
        self.multi_snapshot(self.std_unattached_vol_id, wait=True)

    def test_T3062_std_multi_slow_stopped_vol(self):
        self.multi_snapshot(self.std_stopped_attached_vol_id, wait=True)

    def test_T3063_std_multi_slow_running_vol(self):
        self.multi_snapshot(self.std_running_attached_vol_id, wait=True)

    def test_T3064_std_multi_fast_unattached_vol(self):
        self.multi_snapshot(self.std_unattached_vol_id, wait=False)

    def test_T3065_std_multi_fast_stopped_vol(self):
        self.multi_snapshot(self.std_stopped_attached_vol_id, wait=False)

    def test_T3066_std_multi_fast_running_vol(self):
        self.multi_snapshot(self.std_running_attached_vol_id, wait=False)

    def test_T3067_io1_multi_slow_unattached_vol(self):
        self.multi_snapshot(self.io1_unattached_vol_id, wait=True)

    def test_T3068_io1_multi_slow_stopped_vol(self):
        self.multi_snapshot(self.io1_stopped_attached_vol_id, wait=True)

    def test_T3069_io1_multi_slow_running_vol(self):
        self.multi_snapshot(self.io1_running_attached_vol_id, wait=True)

    def test_T3070_io1_multi_fast_unattached_vol(self):
        self.multi_snapshot(self.io1_unattached_vol_id, wait=False)

    def test_T3071_io1_multi_fast_stopped_vol(self):
        self.multi_snapshot(self.io1_stopped_attached_vol_id, wait=False)

    def test_T3072_io1_multi_fast_running_vol(self):
        self.multi_snapshot(self.io1_running_attached_vol_id, wait=False)

    def test_T3073_gp2_multi_slow_unattached_vol(self):
        self.multi_snapshot(self.gp2_unattached_vol_id, wait=True)

    def test_T3074_gp2_multi_slow_stopped_vol(self):
        self.multi_snapshot(self.gp2_stopped_attached_vol_id, wait=True)

    def test_T3075_gp2_multi_slow_running_vol(self):
        self.multi_snapshot(self.gp2_running_attached_vol_id, wait=True)

    def test_T3076_gp2_multi_fast_unattached_vol(self):
        self.multi_snapshot(self.gp2_unattached_vol_id, wait=False)

    def test_T3077_gp2_multi_fast_stopped_vol(self):
        self.multi_snapshot(self.gp2_stopped_attached_vol_id, wait=False)

    def test_T3078_gp2_multi_fast_running_vol(self):
        self.multi_snapshot(self.gp2_running_attached_vol_id, wait=False)

    def test_T3946_snap_fresh_attached_vol(self):
        inst_info = None
        vol_id = None
        attached = False
        snap_id = None
        try:
            inst_info = create_instances(self.a1_r1, state='running')
            _, [vol_id] = create_volumes(self.a1_r1, state='available')
            self.a1_r1.fcu.AttachVolume(InstanceId=inst_info[INSTANCE_ID_LIST][0], VolumeId=vol_id, Device='/dev/xvdb')
            attached = True
            wait_volumes_state(self.a1_r1, [vol_id], state='in-use')
            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=vol_id).response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap_id])
        finally:
            if snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
                wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=[snap_id])
            if attached:
                self.a1_r1.fcu.DetachVolume(VolumeId=vol_id)
                wait_volumes_state(self.a1_r1, [vol_id], 'available')
            if vol_id:
                delete_volumes(self.a1_r1, [vol_id])
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
