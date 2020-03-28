import datetime
import uuid
import pytest

from qa_common_tools.config.configuration import Configuration
from qa_common_tools.config import config_constants as constants

from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tina.check_tools import create_text_file_volume, format_mount_volume, read_text_file_volume
from qa_tina_tools.tools.tina.create_tools import attach_volume, create_instances_old, create_keypair
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old, delete_keypair
from qa_tina_tools.tina.info_keys import NAME, PATH
from qa_common_tools.ssh import SshTools
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state, wait_snapshots_state
from qa_tina_tools.tools.tina import wait_tools


class Test_create_volume_from_snapshot(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create_volume_from_snapshot, cls).setup_class()
        time_now = datetime.datetime.now()
        unique_id = time_now.strftime('%Y%m%d%H%M%S')
        cls.sg_name = 'sg_T63_{}'.format(unique_id)
        IP_Ingress = Configuration.get('cidr', 'allips')
        cls.public_ip_inst = None
        cls.inst_id = None
        cls.kp_info = None
        cls.sshclient = None
        try:
            # create security group
            sg_response = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=cls.sg_name)
            sg_id = sg_response.response.groupId
            # authorize rules
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupName=cls.sg_name, IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp=IP_Ingress)
            # create keypair
            cls.kp_info = create_keypair(cls.a1_r1)
            # run instance
            ret, id_list = create_instances_old(cls.a1_r1, key_name=cls.kp_info[NAME], security_group_id_list=[sg_id], state='ready')
            cls.inst_id = id_list[0]
            cls.public_ip_inst = ret.response.reservationSet[0].instancesSet[0].ipAddress
            cls.logger.info('PublicIP : {}'.format(cls.public_ip_inst))
            cls.sshclient = SshTools.check_connection_paramiko(cls.public_ip_inst, cls.kp_info[PATH],
                                                               username=cls.a1_r1.config.region.get_info(constants.CENTOS_USER))
        except Exception as error:
            cls.teardown_class()
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            # terminate the instance
            delete_instances_old(cls.a1_r1, [cls.inst_id])

            delete_keypair(cls.a1_r1, cls.kp_info)

            cls.a1_r1.fcu.DeleteSecurityGroup(GroupName=cls.sg_name)

        finally:
            super(Test_create_volume_from_snapshot, cls).teardown_class()

    def create_volume(self, volumeType='standard', IOPS=None, volumeSize=8, drive_letter_code='b', Snapshot_Id=None):

        drive_letter = drive_letter_code
        volume_type = volumeType
        dev = '/dev/xvd{}'.format(drive_letter)
        volume_mount = '/mnt/volume_{}'.format(drive_letter_code)
        size_disk = volumeSize
        ret = None

        if volumeType == 'io1' or volumeType == 'os1':

            ret = self.a1_r1.fcu.CreateVolume(Size=size_disk, VolumeType=volume_type,
                                              AvailabilityZone=self.azs[0], Iops=IOPS)
        else:
            if not Snapshot_Id:

                ret = self.a1_r1.fcu.CreateVolume(Size=size_disk, VolumeType=volume_type,
                                                  AvailabilityZone=self.azs[0])
            else:
                ret = self.a1_r1.fcu.CreateVolume(Size=size_disk, VolumeType=volume_type,
                                                  AvailabilityZone=self.azs[0], SnapshotId=Snapshot_Id)
        volume_id = ret.response.volumeId
        wait_volumes_state(self.a1_r1, [volume_id], state='available', nb_check=5)
        return volume_id, dev, volume_mount

    @pytest.mark.tag_redwire
    def test_T63_create_volume_from_snapshot(self):
        volume_ids = []
        try:
            # create volume /dev/xvdb
            volume_id, device, volume_mount = self.create_volume(volumeType='standard', volumeSize=1, drive_letter_code='b')
            volume_ids.append(volume_id)
            # attach the volume
            attach_volume(self.a1_r1, self.inst_id, volume_id, device)
            # format the volume
            format_mount_volume(self.sshclient, device, volume_mount, True)
            # write some text on the file
            test_file = "test_snapshots.txt"
            text_to_check = uuid.uuid4().hex
            create_text_file_volume(self.sshclient, volume_mount, test_file, text_to_check)
            read_text_file_volume(self.sshclient, volume_mount, test_file, text_to_check)
            # unmount volume to force write to the disk
            cmd = "sudo umount {}".format(device)
            out, _, _ = SshTools.exec_command_paramiko_2(self.sshclient, cmd)
            self.logger.info(out)
            # create a snap
            ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=volume_id)
            snap_id = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap_id])
            # create volume /dev/xvdc
            volume_id_1, device_1, volume_mount_1 = self.create_volume(volumeType='standard', volumeSize=1,
                                                                       drive_letter_code='c', Snapshot_Id=snap_id)
            volume_ids.append(volume_id_1)
            # attach the volume
            attach_volume(self.a1_r1, self.inst_id, volume_id_1, device_1)
            # mount the volume
            format_mount_volume(self.sshclient, device_1, volume_mount_1, False)
            # read from file
            read_text_file_volume(self.sshclient, volume_mount_1, test_file, text_to_check)
        finally:
            try:
                for vol_id in volume_ids:
                    self.a1_r1.fcu.DetachVolume(VolumeId=vol_id)
                wait_volumes_state(self.a1_r1, volume_ids, state='available', cleanup=False)
                for vol_id in volume_ids:
                    self.a1_r1.fcu.DeleteVolume(VolumeId=vol_id)
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            except Exception as error:
                self.logger.exception(error)
                pytest.fail("An unexpected error happened : " + str(error))

    def create_snapshot(self, max_snap=20, volume_id=None):
        for _ in range(max_snap):
            ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=volume_id)
            wait_snapshots_state(self.a1_r1, [ret.response.snapshotId], state='completed')
            self.a1_r1.fcu.DeleteSnapshot(SnapshotId=ret.response.snapshotId)

    def test_T3032_create_snapshot_from_standard_attached_volume(self):
        try:
            drive_letter_code = 'c'
            volume_id, device, _ = self.create_volume(volumeType='standard', volumeSize=1, drive_letter_code=drive_letter_code)
            device = '/dev/xvd{}'.format(drive_letter_code)
            attach_volume(self.a1_r1, self.inst_id, volume_id, device)
            self.create_snapshot(max_snap=5, volume_id=volume_id)
        finally:
            if volume_id:
                self.a1_r1.fcu.DetachVolume(VolumeId=volume_id)
                wait_volumes_state(self.a1_r1, [volume_id], state='available', cleanup=False)
                self.a1_r1.fcu.DeleteVolume(VolumeId=volume_id)

    def test_T3033_create_snapshot_from_gp2_attached_volume(self):
        try:
            drive_letter_code = 'd'
            volume_id, device, _ = self.create_volume(volumeType='gp2', volumeSize=5, drive_letter_code=drive_letter_code)
            device = '/dev/xvd{}'.format(drive_letter_code)
            attach_volume(self.a1_r1, self.inst_id, volume_id, device)
            self.create_snapshot(max_snap=5, volume_id=volume_id)
        finally:
            if volume_id:
                self.a1_r1.fcu.DetachVolume(VolumeId=volume_id)
                wait_volumes_state(self.a1_r1, [volume_id], state='available', cleanup=False)
                self.a1_r1.fcu.DeleteVolume(VolumeId=volume_id)

    def test_T3034_create_snapshot_from_io1_attached_volume(self):
        try:
            drive_letter_code = 'e'
            volume_id, device, _ = self.create_volume(volumeType='io1', volumeSize=5, drive_letter_code=drive_letter_code, IOPS=100)
            device = '/dev/xvd{}'.format(drive_letter_code)
            attach_volume(self.a1_r1, self.inst_id, volume_id, device)
            self.create_snapshot(max_snap=5, volume_id=volume_id)
        finally:
            if volume_id:
                self.a1_r1.fcu.DetachVolume(VolumeId=volume_id)
                wait_volumes_state(self.a1_r1, [volume_id], state='available', cleanup=False)
                self.a1_r1.fcu.DeleteVolume(VolumeId=volume_id)

    def test_T3035_create_snapshot_from_standard_detached_volume(self):
        try:
            drive_letter_code = 'c'
            volume_id, _, _ = self.create_volume(volumeType='standard', volumeSize=1, drive_letter_code=drive_letter_code)
            wait_tools.wait_volumes_state(self.a1_r1, [volume_id], state='available', cleanup=False)
            self.create_snapshot(max_snap=5, volume_id=volume_id)
        finally:
            if volume_id:
                self.a1_r1.fcu.DeleteVolume(VolumeId=volume_id)

    def test_T3036_create_snapshot_from_gp2_detached_volume(self):
        try:
            drive_letter_code = 'd'
            volume_id, _, _ = self.create_volume(volumeType='gp2', volumeSize=5, drive_letter_code=drive_letter_code)
            wait_tools.wait_volumes_state(self.a1_r1, [volume_id], state='available', cleanup=False)
            self.create_snapshot(max_snap=5, volume_id=volume_id)
        finally:
            if volume_id:
                self.a1_r1.fcu.DeleteVolume(VolumeId=volume_id)

    def test_T3037_create_snapshot_from_io1_detached_volume(self):
        try:
            drive_letter_code = 'e'
            volume_id, _, _ = self.create_volume(volumeType='io1', volumeSize=5, drive_letter_code=drive_letter_code, IOPS=100)
            wait_tools.wait_volumes_state(self.a1_r1, [volume_id], state='available', cleanup=False)
            self.create_snapshot(max_snap=5, volume_id=volume_id)
        finally:
            if volume_id:
                self.a1_r1.fcu.DeleteVolume(VolumeId=volume_id)

    def test_T3083_create_snapshot_from_bootdisk(self):
        ret = self.a1_r1.fcu.DescribeVolumes(Filter=[{'Name': 'attachment.instance-id', 'Value': self.inst_id}, {'Name': 'attachment.device', 'Value': '/dev/sda1'}])
        assert len(ret.response.volumeSet) == 1
        self.create_snapshot(max_snap=5, volume_id=ret.response.volumeSet[0].volumeId)

    def test_T4586_create_volume_from_snapshot_without_completed_status(self):
        volume_ids = []
        snap_id = None
        drive_letter_code = 'f'
        try:
            # create volume /dev/xvdb
            volume_id, device, volume_mount = self.create_volume(volumeType='standard', volumeSize=4,
                                                                 drive_letter_code='e')
            volume_ids.append(volume_id)
            # attach the volume
            attach_volume(self.a1_r1, self.inst_id, volume_id, device)
            # format the volume
            format_mount_volume(self.sshclient, device, volume_mount, True)
            # write some text on the file
            test_file = "test_snapshots.txt"
            text_to_check = uuid.uuid4().hex
            create_text_file_volume(self.sshclient, volume_mount, test_file, text_to_check)
            read_text_file_volume(self.sshclient, volume_mount, test_file, text_to_check)
            # unmount volume to force write to the disk
            cmd = "sudo umount {}".format(device)
            out, _, _ = SshTools.exec_command_paramiko_2(self.sshclient, cmd)
            self.logger.info(out)
            # create a snap
            ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=volume_id)
            snap_id = ret.response.snapshotId
            # create volume /dev/xvdc
            ret = self.a1_r1.fcu.CreateVolume(Size=4, VolumeType='standard',
                                              AvailabilityZone=self.azs[0], SnapshotId=snap_id)
            volume_id_1 = ret.response.volumeId
            volume_ids.append(volume_id_1)
            attach_volume(self.a1_r1, self.inst_id, volume_id_1, '/dev/xvd{}'.format(drive_letter_code))

        finally:
            try:
                for vol_id in volume_ids:
                    self.a1_r1.fcu.DetachVolume(VolumeId=vol_id)
                wait_volumes_state(self.a1_r1, volume_ids, state='available', cleanup=False)
                for vol_id in volume_ids:
                    self.a1_r1.fcu.DeleteVolume(VolumeId=vol_id)
                if snap_id:
                    self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            except Exception as error:
                self.logger.exception(error)
                pytest.fail("An unexpected error happened : " + str(error))