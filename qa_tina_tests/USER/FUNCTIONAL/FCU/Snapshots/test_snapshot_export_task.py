from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina import create_tools, wait_tools, delete_tools
from qa_tina_tools.tools.tina import info_keys
from qa_common_tools.ssh import SshTools
from qa_tina_tools.tina.check_tools import format_mount_volume
from qa_tina_tools.tina.setup_tools import write_to_volume
from qa_test_tools.config import config_constants
import pytest

DEVICE = '/dev/xvdb'
MOUNTDIR = 'test_set_dir'
FILENAME = 'test_set_file.txt'
VOL_SIZE = 500
WRITE_SIZE = 100000

@pytest.mark.region_osu
class Test_snapshot_export_task(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        cls.attach_resp = None
        cls.volume_ids = []
        cls.snapshot_ids = []
        cls.max_items = 0
        super(Test_snapshot_export_task, cls).setup_class()
        try:
            ret = cls.a1_r1.fcu.DescribeQuotas(Filter=[{'Name': 'quota.display-name', 'Value': ['Snapshot Exports Limit']},
                                                       {'Name': 'reference', 'Value': ['global']}])
            cls.max_items = ret.response.referenceQuotaSet[0].maxQuotaValue
            # create instance
            cls.inst_info = create_tools.create_instances(cls.a1_r1, state='running')
            # create volumes
            _, cls.volume_ids = create_tools.create_volumes(cls.a1_r1, size=VOL_SIZE, count=2, state='available')
            # attach volumes
            cls.attach_resp = cls.a1_r1.fcu.AttachVolume(Device=DEVICE, InstanceId=cls.inst_info[info_keys.INSTANCE_ID_LIST][0],
                                                         VolumeId=cls.volume_ids[0]).response
            # create ssh client
            cls.sshclient = SshTools.check_connection_paramiko(cls.inst_info[info_keys.INSTANCE_SET][0]['ipAddress'], cls.inst_info[info_keys.KEY_PAIR][info_keys.PATH],
                                                               username=cls.a1_r1.config.region.get_info(config_constants.CENTOS_USER))
            format_mount_volume(cls.sshclient, DEVICE, MOUNTDIR, True)
            write_to_volume(cls.sshclient, MOUNTDIR, FILENAME, WRITE_SIZE)
            cls.snapshot_ids.append(cls.a1_r1.fcu.CreateSnapshot(VolumeId=cls.volume_ids[0]).response.snapshotId)
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.snapshot_ids:
                for snap_id in cls.snapshot_ids:
                    cls.a1_r1.DeleteSnapshot(SnapshotId=snap_id)
            if cls.attach_resp:
                cls.a1_r1.fcu.DetachVolume(VolumeId=cls.volume_ids[0])
                wait_tools.wait_volumes_state(cls.a1_r1, cls.volume_ids, state='available')
            if cls.volume_ids:
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.volume_ids[0])
            if cls.inst_info:
                delete_tools.delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_snapshot_export_task, cls).teardown_class()

    def test_verify_no_tasks(self):
        ret = self.a1_r1.fcu.DescribeQuotas(Filter=[{'Name': 'quota.display-name', 'Value': ['Snapshot Exports Limit']},
                                                    {'Name': 'reference', 'Value': ['global']}])
        assert self.max_items == ret.response.referenceQuotaSet[0].maxQuotaValue
        assert 0 == ret.response.referenceQuotaSet[0].usedQuotaValue
 
    def test_create_export_tasks(self):
        for _ in range(self.max_items):
            self.a1_r1.fcu.CreateSnapshotExportTask
