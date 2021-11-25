import time
import pytest
from qa_test_tools.config import config_constants
from qa_common_tools.ssh import SshTools
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import wait, oapi, info_keys, check_tools
from qa_tina_tools.tina.check_tools import format_mount_volume, umount_volume
from qa_tina_tests.USER.API.OAPI.Snapshot.Snapshot import validate_snasphot

DEVICE_NAME = '/dev/xvdc'
CMD = 'ls -lsa /dev/x*'

# NB_ITER is the number of iteration in this test.
# The assigned value is requested in pqa-2774.
NB_ITER_1 = 50
NB_ITER_2 = 500

class Test_attach_detach_volume(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_attach_detach_volume, cls).setup_class()
        cls.vm_info = None
        cls.sshclient = None
        cls.vol_id = None
        cls.ret_link = None
        cls.volume_mount = None
        cls.is_attached = False
        cls.snap_ids = None

    @classmethod
    def teardown_class(cls):
        super(Test_attach_detach_volume, cls).teardown_class()

    def setup_method(self, method):
        super(Test_attach_detach_volume, self).setup_method(method)
        self.volume_mount = '/mnt/vol'
        self.snap_ids = []
        try:
            self.vm_info = oapi.create_Vms(self.a1_r1, state='ready')

            self.vol_id = self.a1_r1.oapi.CreateVolume(VolumeType='standard', Size=2,
                                                        SubregionName=self.azs[0]).response.Volume.VolumeId

            wait.wait_Volumes_state(self.a1_r1, [self.vol_id], state='available')

            self.ret_link = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id,
                                                        VmId=self.vm_info[info_keys.VM_IDS][0],
                                                        DeviceName=DEVICE_NAME)
            self.is_attached = True

            wait.wait_Volumes_state(self.a1_r1, [self.vol_id], state='in-use')

            self.sshclient = check_tools.check_ssh_connection(self.a1_r1, self.vm_info[info_keys.VMS][0]['VmId'],
                                                              self.vm_info[info_keys.VMS][0]['PublicIp'],
                                                              self.vm_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                              self.a1_r1.config.region.get_info(config_constants.CENTOS_USER))

            format_mount_volume(self.sshclient, DEVICE_NAME, self.volume_mount, True)
            time.sleep(2)
            umount_volume(self.sshclient, self.volume_mount)

            self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id)
            self.is_attached = False
            wait.wait_Volumes_state(self.a1_r1, [self.vol_id], state='available')
        except:
            try:
                self.teardown_method(method)
            finally:
                raise

    def teardown_method(self, method):
        try:
            if self.is_attached:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id)
                wait.wait_Volumes_state(self.a1_r1, [self.vol_id], state='available')
            if self.snap_ids:
                for snap_id in self.snap_ids:
                    self.a1_r1.oapi.DeleteSnapshot(SnapshotId=snap_id)
                wait.wait_Snapshots_state(self.a1_r1, self.snap_ids, cleanup=True)
            if self.vol_id:
                self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol_id)
            if self.vm_info:
                oapi.delete_Vms(self.a1_r1, self.vm_info)
        except Exception as error:
            self.logger.exception(error)
            pytest.fail("An unexpected error happened : " + str(error))
        finally:
            super(Test_attach_detach_volume, self).teardown_method(method)

    def test_T5649_multi_snap_and_attach_detach(self):
        """
            This test have two goal.
            The first loop aim to create snapshot
            The second loop aim to attach a volume and mount it,
            then umount and detach volume.
        """
        for _ in range(NB_ITER_1):
            try:
                ret = self.a1_r1.oapi.CreateSnapshot(VolumeId=self.vol_id, Description='hello').response.Snapshot
                self.snap_ids.append(ret.SnapshotId)

                wait.wait_Snapshots_state(self.a1_r1, self.snap_ids, state='completed')

                validate_snasphot(ret, expected_snap={
                    'Description': 'hello',
                    'AccountId': self.a1_r1.config.account.account_id,
                    'VolumeSize': 2,
                })
                assert ret.State is not None
            except Exception as error:
                self.logger.exception(error)
                pytest.fail("An unexpected error happened : " + str(error))

        for _ in range(NB_ITER_1):
            try:
                self.ret_link = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id,
                                                            VmId=self.vm_info[info_keys.VM_IDS][0],
                                                            DeviceName=DEVICE_NAME)
                self.is_attached = True

                wait.wait_Volumes_state(self.a1_r1, [self.vol_id], state='in-use')

                out, status, _ = SshTools.exec_command_paramiko(self.sshclient, CMD)
                assert status == 0
                assert DEVICE_NAME in out

                cmd_mount = 'sudo mount -o nouuid {} {}'.format(DEVICE_NAME, self.volume_mount)
                SshTools.exec_command_paramiko(self.sshclient, cmd_mount)

                time.sleep(2)

                umount_volume(self.sshclient, self.volume_mount)
            except Exception as error:
                self.logger.exception(error)
                pytest.fail("An unexpected error happened : " + str(error))
            finally:
                if self.ret_link:
                    self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id)
                    self.is_attached = False
                    wait.wait_Volumes_state(self.a1_r1, [self.vol_id], state='available')

                    _, status, _ = SshTools.exec_command_paramiko(self.sshclient, CMD, expected_status=2)
                    assert status != 0

    def test_T5650_create_snap_from_attached_volume(self):
        """
            This test aim to attach a volume and mount it,
            then create a snapshot from attached volume.
        """
        try:
            self.ret_link = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id,
                                                        VmId=self.vm_info[info_keys.VM_IDS][0],
                                                        DeviceName=DEVICE_NAME)
            self.is_attached = True

            wait.wait_Volumes_state(self.a1_r1, [self.vol_id], state='in-use')

            out, status, _ = SshTools.exec_command_paramiko(self.sshclient, CMD)
            assert status == 0
            assert DEVICE_NAME in out

            cmd_mount = 'sudo mount -o nouuid {} {}'.format(DEVICE_NAME, self.volume_mount)
            SshTools.exec_command_paramiko(self.sshclient, cmd_mount)
            time.sleep(2)

            for _ in range(NB_ITER_2):
                try:
                    ret = self.a1_r1.oapi.CreateSnapshot(VolumeId=self.vol_id, Description='hello').response.Snapshot
                    self.snap_ids.append(ret.SnapshotId)

                    wait.wait_Snapshots_state(self.a1_r1, [ret.SnapshotId], state='completed')

                    validate_snasphot(ret, expected_snap={
                        'Description': 'hello',
                        'AccountId': self.a1_r1.config.account.account_id,
                        'VolumeSize': 2,
                    })
                    assert ret.State is not None
                except Exception as error:
                    self.logger.exception(error)
                    pytest.fail("An unexpected error happened : " + str(error))

            umount_volume(self.sshclient, self.volume_mount)
        except Exception as error:
            self.logger.exception(error)
            pytest.fail("An unexpected error happened : " + str(error))
        finally:
            if self.ret_link:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id)
                self.is_attached = False
                wait.wait_Volumes_state(self.a1_r1, [self.vol_id], state='available')

                _, status, _ = SshTools.exec_command_paramiko(self.sshclient, CMD, expected_status=2)
                assert status != 0

    def test_T5651_attach_detach_vol_and_create_snap(self):
        """
            This test aim to attach a volume and mount it,
            write text file and umount and detach volume,
            then create a snapshot for volume.
        """
        for _ in range(NB_ITER_1):
            try:
                self.ret_link = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id,
                                                            VmId=self.vm_info[info_keys.VM_IDS][0],
                                                            DeviceName=DEVICE_NAME)
                self.is_attached = True

                wait.wait_Volumes_state(self.a1_r1, [self.vol_id], state='in-use')

                out, status, _ = SshTools.exec_command_paramiko(self.sshclient, CMD)
                assert status == 0
                assert DEVICE_NAME in out

                cmd_mount = 'sudo mount -o nouuid {} {}'.format(DEVICE_NAME, self.volume_mount)
                SshTools.exec_command_paramiko(self.sshclient, cmd_mount)

                cmd_write_data = 'sudo openssl rand -out /mnt/vol/data_xxx.txt -base64 $(({} * 2**20 * 3/4))'.format(100)
                SshTools.exec_command_paramiko(self.sshclient, cmd_write_data, eof_time_out=300)

                umount_volume(self.sshclient, self.volume_mount)
                if self.ret_link:
                    self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id)
                    wait.wait_Volumes_state(self.a1_r1, [self.vol_id], state='available')
                    self.is_attached = False

                    _, status, _ = SshTools.exec_command_paramiko(self.sshclient, CMD, expected_status=2)
                    assert status != 0

                    try:
                        ret = self.a1_r1.oapi.CreateSnapshot(VolumeId=self.vol_id, Description='hello').response.Snapshot
                        self.snap_ids.append(ret.SnapshotId)

                        wait.wait_Snapshots_state(self.a1_r1, self.snap_ids, state='completed')

                        validate_snasphot(ret, expected_snap={
                            'Description': 'hello',
                            'AccountId': self.a1_r1.config.account.account_id,
                            'VolumeSize': 2,
                        })
                        assert ret.State is not None
                    except Exception as error:
                        self.logger.exception(error)
                        pytest.fail("An unexpected error happened : " + str(error))
            except Exception as error:
                self.logger.exception(error)
                pytest.fail("An unexpected error happened : " + str(error))
