

import uuid

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.check_tools import create_text_file_volume, format_mount_volume, check_volume
from qa_tina_tools.tools.tina import wait_tools
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, INSTANCE_SET, KEY_PAIR, PATH


class Test_snapshot(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_snapshot, cls).setup_class()
        cls.inst_info = {}
        cls.volume_ids = []
        cls.snapshot_ids = []
        drive_letter = 'b'
        cls.device = '/dev/xvd{}'.format(drive_letter)
        cls.volume_mount = '/mnt/volume_{}'.format(drive_letter)

        cls.vol1_id = []
        cls.ret_attach = None
        cls.sshclient = None

        cls.size = 10
        try:
            cls.inst_info = create_instances(cls.a1_r1, state='ready')
            _, cls.vol1_id = create_volumes(cls.a1_r1, state='available')
            cls.volume_ids.append(cls.vol1_id[0])
            cls.ret_attach = cls.a1_r1.fcu.AttachVolume(InstanceId=cls.inst_info[INSTANCE_ID_LIST][0], VolumeId=cls.vol1_id[0], Device=cls.device)
            wait_tools.wait_volumes_state(cls.a1_r1, cls.vol1_id, state='in-use')
            cls.sshclient = SshTools.check_connection_paramiko(cls.inst_info[INSTANCE_SET][0]['ipAddress'], cls.inst_info[KEY_PAIR][PATH],
                                                               username=cls.a1_r1.config.region.get_info(constants.CENTOS_USER))
            #format/mount
            format_mount_volume(cls.sshclient, cls.device, cls.volume_mount, True)
            # write
            cls.text_to_check = uuid.uuid4().hex
            cls.test_file = "test_snapshot.txt"
            create_text_file_volume(cls.sshclient, cls.volume_mount, cls.test_file, cls.text_to_check)
            #umount
            cmd = 'sudo umount {}'.format(cls.volume_mount)
            SshTools.exec_command_paramiko(cls.sshclient, cmd)
        except Exception as error:
            cls.teardown_class()
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret_attach:
                cls.a1_r1.fcu.DetachVolume(VolumeId=cls.vol1_id[0])
                wait_tools.wait_volumes_state(cls.a1_r1, cls.vol1_id, state='available')
            if cls.volume_ids:
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.vol1_id[0])
                wait_tools.wait_volumes_state(cls.a1_r1, volume_id_list=cls.vol1_id, cleanup=True)
            if cls.inst_info:
                cls.a1_r1.fcu.StopInstances(InstanceId=cls.inst_info[INSTANCE_ID_LIST][0])
                wait_tools.wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=cls.inst_info[INSTANCE_ID_LIST], state='stopped')
                cls.a1_r1.fcu.TerminateInstances(InstanceId=cls.inst_info[INSTANCE_ID_LIST][0])
                wait_tools.wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=cls.inst_info[INSTANCE_ID_LIST], state='terminated')
        finally:
            super(Test_snapshot, cls).teardown_class()

    def test_T4305_simple_snapshot(self):
        vol2_id = None
        snap1_id = None
        attached = None
        mounted = False
        drive_letter = 'c'
        device = '/dev/xvd{}'.format(drive_letter)
        volume_mount = '/mnt/volume_{}'.format(drive_letter)

        try:
            snap1_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=self.vol1_id[0]).response.snapshotId
            wait_tools.wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap1_id])
            self.snapshot_ids.append(snap1_id)
            vol2_id = self.a1_r1.fcu.CreateVolume(AvailabilityZone=self.a1_r1.config.region.az_name,
                                                  SnapshotId=snap1_id, Size=self.size).response.volumeId
            wait_tools.wait_volumes_state(self.a1_r1, [vol2_id], state='available')
            self.volume_ids.append(vol2_id)
            attached = self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], VolumeId=vol2_id, Device=device)
            wait_tools.wait_volumes_state(self.a1_r1, [vol2_id], state='in-use')
            self.sshclient = SshTools.check_connection_paramiko(self.inst_info[INSTANCE_SET][0]['ipAddress'], self.inst_info[KEY_PAIR][PATH],
                                                                username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # mount the volume
            cmd = 'sudo mkdir {}'.format(volume_mount)
            self.logger.info("Executing: %s", cmd)
            SshTools.exec_command_paramiko(self.sshclient, cmd)
            cmd = 'sudo mount ' + device + ' ' + volume_mount
            self.logger.info("Executing: %s", cmd)
            SshTools.exec_command_paramiko(self.sshclient, cmd)
            mounted = True
            # check data
            check_volume(self.sshclient, device, self.size, with_format=False, text_to_check=self.text_to_check, test_file=self.test_file)

        finally:
            if mounted:
                cmd = 'sudo umount {}'.format(volume_mount)
                SshTools.exec_command_paramiko(self.sshclient, cmd)
            if attached:
                self.a1_r1.fcu.DetachVolume(VolumeId=vol2_id)
                wait_tools.wait_volumes_state(self.a1_r1, [vol2_id], state='available')
            if vol2_id:
                self.a1_r1.fcu.DeleteVolume(VolumeId=vol2_id)
                wait_tools.wait_volumes_state(self.a1_r1, volume_id_list=[vol2_id], cleanup=True)
            if self.snapshot_ids:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap1_id)
                wait_tools.wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=[snap1_id])
