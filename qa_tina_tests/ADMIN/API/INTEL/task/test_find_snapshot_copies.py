from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_volumes, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_volumes, delete_instances
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state, wait_volumes_state, wait_instances_state
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, KEY_PAIR, INSTANCE_SET, PATH
from qa_common_tools.ssh import SshTools
from qa_common_tools.config import config_constants as constants


DEVICE = '/dev/xvdc'
MOUNT_DIR = 'mountdir'
SIZE_GB = 500


class Test_find_snapshot_copies(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_find_snapshot_copies, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_find_snapshot_copies, cls).teardown_class()

    def test_T2287_no_params(self):
        inst_info = None
        vol_id = None
        snap_id = None
        snap_ids = []
        # create snapshot copy tasks
        try:
            inst_info = create_instances(self.a1_r1)
            _, [vol_id] = create_volumes(self.a1_r1, state='available', size=SIZE_GB)
            wait_volumes_state(self.a1_r1, [vol_id], 'available')
            self.a1_r1.fcu.AttachVolume(InstanceId=inst_info[INSTANCE_ID_LIST][0], VolumeId=vol_id, Device=DEVICE)
            wait_volumes_state(self.a1_r1, [vol_id], state='in-use')

            wait_instances_state(self.a1_r1, inst_info[INSTANCE_ID_LIST], state='ready')
            sshclient = SshTools.check_connection_paramiko(inst_info[INSTANCE_SET][0]['ipAddress'], inst_info[KEY_PAIR][PATH],
                                                           username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

            # format / mount /write to volume
            cmd = 'sudo mkfs.ext4 -F {}'.format(DEVICE)
            self.logger.info("Executing: %s", cmd)
            out, status, err = SshTools.exec_command_paramiko_2(sshclient, cmd)
            cmd = 'sudo mkdir {}'.format(MOUNT_DIR)
            self.logger.info("Executing: %s", cmd)
            out, status, err = SshTools.exec_command_paramiko_2(sshclient, cmd)
            cmd = 'sudo mount ' + DEVICE + ' ' + MOUNT_DIR
            self.logger.info("Executing: %s", cmd)
            out, status, err = SshTools.exec_command_paramiko_2(sshclient, cmd)
            cmd = 'cd  ' + MOUNT_DIR
            self.logger.info("Executing: %s", cmd)
            out, status, err = SshTools.exec_command_paramiko_2(sshclient, cmd)
            cmd = 'sudo openssl rand -out ' + MOUNT_DIR + '.txt -base64 $((' + str(SIZE_GB - 100) + ' * 2**30 * 3/4))'
            self.logger.info("Executing: %s", cmd)
            out, status, err = SshTools.exec_command_paramiko_2(sshclient, cmd)

            self.a1_r1.fcu.DetachVolume(InstanceId=inst_info[INSTANCE_ID_LIST][0], VolumeId=vol_id)
            wait_volumes_state(self.a1_r1, [vol_id], state='available')

            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=vol_id).response.snapshotId
            wait_snapshots_state(self.a1_r1, [snap_id], state='completed')
            self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=snap_id,
                                                   CreateVolumePermission={'Add': [{'UserId': self.a2_r1.config.account.account_id}]})
            for _ in range(5):
                snap_ids.append(self.a2_r1.fcu.CopySnapshot(SourceRegion=self.a1_r1.config.region.name,
                                                            SourceSnapshotId=snap_id).response.snapshotId)
            ret = self.a2_r1.intel.task.find_snapshot_copies()
            for res in ret.response.result:
                assert res.start_date
                assert res.completion_date
            wait_snapshots_state(self.a2_r1, snap_ids, state='completed')
        except Exception as error:
            print('kjgkgh')
        finally:
            wait_snapshots_state(self.a2_r1, snap_ids, state='completed')
            for snap_id in snap_ids:
                try:
                    self.a2_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
                except:
                    pass
            if snap_id:
                try:
                    self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
                except:
                    pass
            if vol_id:
                try:
                    delete_volumes(self.a1_r1, [vol_id])
                except:
                    pass
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
