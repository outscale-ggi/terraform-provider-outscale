import pytest

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina import info_keys, wait_tools
from qa_tina_tools.tina.check_tools import format_mount_volume
from qa_tina_tools.tina.setup_tools import write_to_volume
from qa_tina_tools.tools.tina import create_tools, delete_tools

DEVICE = '/dev/xvdb'
MOUNTDIR = 'test_set_dir'
FILENAME = 'test_set_file.txt'
VOL_SIZE = 50
WRITE_SIZE = 10
NB_SNAP_VOL = 10

@pytest.mark.region_admin
class Test_volume_gc(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_volume_gc, cls).setup_class()
        cls.inst_info = None
        cls.attach_resp = None
        cls.volume_id = None
        cls.snapshot_ids = []

    @classmethod
    def teardown_class(cls):
        super(Test_volume_gc, cls).teardown_class()

    def setup_method(self, method):
        super(Test_volume_gc, self).setup_method(method)
        self.inst_info = None
        self.attach_resp = None
        self.volume_id = None
        self.snapshot_ids = []
        try:
            # create instance
            self.inst_info = create_tools.create_instances(self.a1_r1, state='running')
            # create volumes
            _, [self.volume_id] = create_tools.create_volumes(self.a1_r1, size=VOL_SIZE, state='available')
            # attach volumes
            self.attach_resp = self.a1_r1.fcu.AttachVolume(Device=DEVICE,
                                                           InstanceId=self.inst_info[info_keys.INSTANCE_ID_LIST][0],
                                                           VolumeId=self.volume_id).response
            # wait instance is ready
            wait_tools.wait_instances_state(self.a1_r1, self.inst_info[info_keys.INSTANCE_ID_LIST], state='ready')
            # create ssh client
            sshclient = SshTools.check_connection_paramiko(self.inst_info[info_keys.INSTANCE_SET][0]['ipAddress'],
                                                           self.inst_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                           username=self.a1_r1.config.region.get_info(
                                                               config_constants.CENTOS_USER))
            format_mount_volume(sshclient, DEVICE, MOUNTDIR, True)
            # write into the vol
            write_to_volume(sshclient, MOUNTDIR, FILENAME, WRITE_SIZE)
            # detach vol
            if self.attach_resp:
                self.a1_r1.fcu.DetachVolume(VolumeId=self.volume_id)
                wait_tools.wait_volumes_state(self.a1_r1, [self.volume_id], state='available')

        except Exception as error:
            try:
                self.teardown_method(method)
            except Exception as err:
                raise err
            finally:
                raise error

    def teardown_method(self, method):
        try:
            if self.snapshot_ids:
                for snap_id in self.snapshot_ids:
                    self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            if self.volume_id:
                self.a1_r1.fcu.DeleteVolume(VolumeId=self.volume_id)
                self.volume_id = None
            if self.inst_info:
                delete_tools.delete_instances(self.a1_r1, self.inst_info)
        finally:
            super(Test_volume_gc, self).teardown_method(method)

    def test_T6067_volume_gc_valid_call(self):
        vol_id = self.volume_id
        # create snapshots
        for _ in range(NB_SNAP_VOL):
            self.snapshot_ids.append(self.a1_r1.fcu.CreateSnapshot(VolumeId=vol_id).response.snapshotId)
        self.a1_r1.fcu.DeleteVolume(VolumeId=vol_id)
        self.volume_id = None
        self.a1_r1.intel.volume.gc()
        wait_tools.wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=self.snapshot_ids)
        if vol_id:
            ret = self.a1_r1.intel.volume.find(id=vol_id).response.result
            assert len(ret) == 0
