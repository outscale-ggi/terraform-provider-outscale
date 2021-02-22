import datetime
import uuid
from string import ascii_lowercase

import pytest

from qa_common_tools.ssh import SshTools
from qa_test_tools.misc import id_generator
from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import check_tools
from qa_tina_tools.tina.check_tools import create_text_file_volume, format_mount_volume, read_text_file_volume
from qa_tina_tools.tina.info_keys import NAME, PATH
from qa_tina_tools.tools.tina import wait_tools
from qa_tina_tools.tools.tina.create_tools import attach_volume, create_instances_old, create_keypair
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old, delete_keypair
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state, wait_snapshots_state, \
    wait_snapshot_export_tasks_state


class Test_create_volume_from_snapshot(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create_volume_from_snapshot, cls).setup_class()
        time_now = datetime.datetime.now()
        unique_id = time_now.strftime('%Y%m%d%H%M%S')
        cls.sg_name = 'sg_T63_{}'.format(unique_id)
        ip_ingress = Configuration.get('cidr', 'allips')
        cls.public_ip_inst = None
        cls.public_ip_inst_storage = None
        cls.inst_id = None
        cls.inst_id_storage = None
        cls.kp_info = None
        cls.sshclient = None
        cls.sshclient_storage = None
        try:
            # create security group
            sg_response = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=cls.sg_name)
            sg_id = sg_response.response.groupId
            # authorize rules
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupName=cls.sg_name, IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp=ip_ingress)
            # create keypair
            cls.kp_info = create_keypair(cls.a1_r1)
            # run instance
            ret, id_list = create_instances_old(cls.a1_r1, num=2, key_name=cls.kp_info[NAME], security_group_id_list=[sg_id], state='ready')
            cls.inst_id = id_list[1]
            cls.inst_id_storage = id_list[0]
            cls.public_ip_inst = ret.response.reservationSet[0].instancesSet[0].ipAddress
            cls.public_ip_inst_storage = ret.response.reservationSet[0].instancesSet[1].ipAddress

            cls.logger.info('PublicIP : %s', cls.public_ip_inst)
            cls.sshclient = check_tools.check_ssh_connection(cls.a1_r1, cls.inst_id, cls.public_ip_inst, cls.kp_info[PATH],
                                                             username=cls.a1_r1.config.region.get_info(constants.CENTOS_USER))
            cls.sshclient_storage = check_tools.check_ssh_connection(cls.a1_r1, cls.inst_id_storage, cls.public_ip_inst_storage,
                                                                     cls.kp_info[PATH], username=cls.a1_r1.config.region.
                                                                     get_info(constants.CENTOS_USER))
            # cls.sshclient = SshTools.check_connection_paramiko(cls.public_ip_inst, cls.kp_info[PATH],
            # username=cls.a1_r1.config.region.get_info(constants.CENTOS_USER))
        except Exception as error:
            cls.teardown_class()
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            # terminate the instance
            delete_instances_old(cls.a1_r1, [cls.inst_id, cls.inst_id_storage])

            delete_keypair(cls.a1_r1, cls.kp_info)

            cls.a1_r1.fcu.DeleteSecurityGroup(GroupName=cls.sg_name)

        finally:
            super(Test_create_volume_from_snapshot, cls).teardown_class()

    def create_volume(self, volume_type='standard', iops=None, volume_size=8, drive_letter_code='b', snapshot_id=None):

        drive_letter = drive_letter_code
        type_of_volume = volume_type
        dev = '/dev/xvd{}'.format(drive_letter)
        volume_mount = '/mnt/volume_{}'.format(drive_letter_code)
        size_disk = volume_size
        ret = None

        if type_of_volume in ['io1', 'os1']:

            ret = self.a1_r1.fcu.CreateVolume(Size=size_disk, VolumeType=type_of_volume, AvailabilityZone=self.azs[0], Iops=iops)
        else:
            if not snapshot_id:
                ret = self.a1_r1.fcu.CreateVolume(Size=size_disk, VolumeType=type_of_volume, AvailabilityZone=self.azs[0])
            else:
                ret = self.a1_r1.fcu.CreateVolume(Size=size_disk, VolumeType=type_of_volume, AvailabilityZone=self.azs[0], SnapshotId=snapshot_id)
        volume_id = ret.response.volumeId
        wait_volumes_state(self.a1_r1, [volume_id], state='available', nb_check=5)
        return volume_id, dev, volume_mount

    @pytest.mark.tag_redwire
    def test_T63_create_volume_from_snapshot(self):
        volume_ids = []
        snap_id = None
        try:
            # create volume /dev/xvdb
            volume_id, device, volume_mount = self.create_volume(volume_type='standard', volume_size=1, drive_letter_code='b')
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
            out, _, _ = SshTools.exec_command_paramiko(self.sshclient, cmd)
            self.logger.info(out)
            # create a snap
            ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=volume_id)
            snap_id = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap_id])
            # create volume /dev/xvdc
            volume_id_1, device_1, volume_mount_1 = self.create_volume(volume_type='standard', volume_size=1,
                                                                       drive_letter_code='c', snapshot_id=snap_id)
            volume_ids.append(volume_id_1)
            # attach the volume
            attach_volume(self.a1_r1, self.inst_id, volume_id_1, device_1)
            # mount the volume
            format_mount_volume(self.sshclient, device_1, volume_mount_1, False)
            # read from file
            read_text_file_volume(self.sshclient, volume_mount_1, test_file, text_to_check)
        finally:
            try:
                if volume_ids:
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

    @pytest.mark.region_storageservice
    def test_T5449_create_volume_from_imported_snapshot_from_storageservice(self):
        volume_ids = []
        snap_id = None
        supported_snap_types = ['qcow2']
        bucket_name = id_generator(prefix='snap', chars=ascii_lowercase)
        key = None
        try:
            # create volume /dev/xvdb
            volume_id, device, volume_mount = self.create_volume(volume_type='standard', volume_size=1, drive_letter_code='b')
            volume_ids.append(volume_id)
            # attach the volume
            attach_volume(self.a1_r1, self.inst_id_storage, volume_id, device)
            # format the volume
            format_mount_volume(self.sshclient_storage, device, volume_mount, True)
            # write some text on the file
            test_file = "test_snapshots.txt"
            text_to_check = uuid.uuid4().hex
            create_text_file_volume(self.sshclient_storage, volume_mount, test_file, text_to_check)
            read_text_file_volume(self.sshclient_storage, volume_mount, test_file, text_to_check)
            # unmount volume to force write to the disk
            cmd = "sudo umount {}".format(device)
            out, _, _ = SshTools.exec_command_paramiko(self.sshclient_storage, cmd)
            self.logger.info(out)
            # create a snap
            ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=volume_id)
            snap_id = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap_id])
            ret = self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=snap_id,
                                                          ExportToOsu={'DiskImageFormat': supported_snap_types[0], 'OsuBucket': bucket_name})
            task_id = ret.response.snapshotExportTask.snapshotExportTaskId
            wait_snapshot_export_tasks_state(osc_sdk=self.a1_r1, state='completed', snapshot_export_task_id_list=[task_id])
            k_list = self.a1_r1.storageservice.list_objects(Bucket=bucket_name)
            if 'Contents' in list(k_list.keys()):
                key = k_list['Contents'][0]['Key']
            else:
                assert False, "Key not found on storageservice"
            params = {'Bucket': bucket_name, 'Key': key}
            url = self.a1_r1.storageservice.generate_presigned_url(ClientMethod='get_object', Params=params,
                                                                   ExpiresIn=3600)
            ret = self.a1_r1.fcu.DescribeSnapshots(SnapshotId=[snap_id])
            size = ret.response.snapshotSet[0].volumeSize
            gb_to_byte = int(size) * pow(1024, 3)
            ret = self.a1_r1.fcu.ImportSnapshot(snapshotLocation=url, snapshotSize=gb_to_byte,
                                                description='This is a snapshot test')
            snap_id_imported = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap_id_imported])
            # create volume /dev/xvdc
            volume_id_1, device_1, volume_mount_1 = self.create_volume(volume_type='standard', volume_size=1,
                                                                       drive_letter_code='c', snapshot_id=snap_id)
            volume_ids.append(volume_id_1)
            # attach the volume
            attach_volume(self.a1_r1, self.inst_id_storage, volume_id_1, device_1)
            # mount the volume
            format_mount_volume(self.sshclient_storage, device_1, volume_mount_1, False)
            # read from file
            read_text_file_volume(self.sshclient_storage, volume_mount_1, test_file, text_to_check)
        finally:
            try:
                if volume_ids:
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

    def create_snapshot(self, max_snap=20, volume_id=None):
        for _ in range(max_snap):
            ret = self.a1_r1.fcu.CreateSnapshot(VolumeId=volume_id)
            wait_snapshots_state(self.a1_r1, [ret.response.snapshotId], state='completed')
            self.a1_r1.fcu.DeleteSnapshot(SnapshotId=ret.response.snapshotId)

    def test_T3032_create_snapshot_from_standard_attached_volume(self):
        try:
            drive_letter_code = 'c'
            volume_id, device, _ = self.create_volume(volume_type='standard', volume_size=1, drive_letter_code=drive_letter_code)
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
            volume_id, device, _ = self.create_volume(volume_type='gp2', volume_size=5, drive_letter_code=drive_letter_code)
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
            volume_id, device, _ = self.create_volume(volume_type='io1', volume_size=5, drive_letter_code=drive_letter_code, iops=100)
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
            volume_id, _, _ = self.create_volume(volume_type='standard', volume_size=1, drive_letter_code=drive_letter_code)
            wait_tools.wait_volumes_state(self.a1_r1, [volume_id], state='available', cleanup=False)
            self.create_snapshot(max_snap=5, volume_id=volume_id)
        finally:
            if volume_id:
                self.a1_r1.fcu.DeleteVolume(VolumeId=volume_id)

    def test_T3036_create_snapshot_from_gp2_detached_volume(self):
        try:
            drive_letter_code = 'd'
            volume_id, _, _ = self.create_volume(volume_type='gp2', volume_size=5, drive_letter_code=drive_letter_code)
            wait_tools.wait_volumes_state(self.a1_r1, [volume_id], state='available', cleanup=False)
            self.create_snapshot(max_snap=5, volume_id=volume_id)
        finally:
            if volume_id:
                self.a1_r1.fcu.DeleteVolume(VolumeId=volume_id)

    def test_T3037_create_snapshot_from_io1_detached_volume(self):
        try:
            drive_letter_code = 'e'
            volume_id, _, _ = self.create_volume(volume_type='io1', volume_size=5, drive_letter_code=drive_letter_code, iops=100)
            wait_tools.wait_volumes_state(self.a1_r1, [volume_id], state='available', cleanup=False)
            self.create_snapshot(max_snap=5, volume_id=volume_id)
        finally:
            if volume_id:
                self.a1_r1.fcu.DeleteVolume(VolumeId=volume_id)

    def test_T3083_create_snapshot_from_bootdisk(self):
        ret = self.a1_r1.fcu.DescribeVolumes(Filter=[{'Name': 'attachment.instance-id', 'Value': self.inst_id},
                                                     {'Name': 'attachment.device', 'Value': '/dev/sda1'}])
        assert len(ret.response.volumeSet) == 1
        self.create_snapshot(max_snap=5, volume_id=ret.response.volumeSet[0].volumeId)

    def test_T4586_create_volume_from_snapshot_without_completed_status(self):
        volume_ids = []
        snap_id = None
        drive_letter_code = 'f'
        try:
            # create volume /dev/xvdb
            volume_id, device, volume_mount = self.create_volume(volume_type='standard', volume_size=4,
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
            out, _, _ = SshTools.exec_command_paramiko(self.sshclient, cmd)
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
