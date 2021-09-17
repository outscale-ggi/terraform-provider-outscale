

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state

NB_SNAP = 3


class Test_DescribeSnapshots(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeSnapshots, cls).setup_class()
        cls.snap_ids = []  # snapshots ids for user1
        cls.vol_id = None  # volumes ids for user1
        try:
            _, [cls.vol_id] = create_volumes(cls.a1_r1, state="available")
            for _ in range(NB_SNAP):
                snap_id = cls.a1_r1.fcu.CreateSnapshot(VolumeId=cls.vol_id).response.snapshotId
                cls.snap_ids.append(snap_id)
                wait_snapshots_state(cls.a1_r1, [snap_id], state="completed")
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.snap_ids:
                for snap_id in cls.snap_ids:
                    cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            if cls.vol_id:
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.vol_id)
        finally:
            super(Test_DescribeSnapshots, cls).teardown_class()

    def test_T3187_from_other_account(self):
        try:
            self.a2_r1.fcu.DescribeSnapshots(SnapshotId=self.snap_ids[0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshot.NotFound', "The snapshot '" + self.snap_ids[0] + "' does not exist.")

#    def test_TXXX_filter_restorable_by(self):
#        _, vol_id_list = create_volumes(osc_sdk=self.a1_r1, state='available')
#        snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=vol_id_list[0]).response.snapshotId
#        wait_snapshots_state(self.a1_r1, [snap_id], 'completed')
#        self.a1_r1.fcu.ModifySnapshotAttribute(SnapshotId=snap_id,
#                                               CreateVolumePermission={'Add': [{'UserId': self.a2_r1.config.account.account_id}]})
#        ret1 = self.a1_r1.fcu.DescribeSnapshots(RestorableBy=[self.a1_r1.config.account.account_id])
#        ret2 = self.a1_r1.fcu.DescribeSnapshots(RestorableBy=[self.a2_r1.config.account.account_id])
#        ret3 = self.a2_r1.fcu.DescribeSnapshots(RestorableBy=[self.a1_r1.config.account.account_id])
#        ret4 = self.a2_r1.fcu.DescribeSnapshots(RestorableBy=[self.a2_r1.config.account.account_id])
#        print('toto')

    def test_T5953_with_tag_filters(self):
        self.a1_r1.fcu.CreateTags(ResourceId=self.snap_ids[0:1], Tag=[{'Key': 'key1', 'Value': 'value2'}, {'Key': 'key2', 'Value': 'value3'}])
        self.a1_r1.fcu.CreateTags(ResourceId=self.snap_ids[1:2], Tag=[{'Key': 'key2', 'Value': 'value1'}, {'Key': 'key3', 'Value': 'value2'}])
        self.a1_r1.fcu.CreateTags(ResourceId=self.snap_ids[2:3], Tag=[{'Key': 'key3', 'Value': 'value1'}, {'Key': 'key1', 'Value': 'value3'}])

        ret = self.a1_r1.fcu.DescribeSnapshots(Filter=[{'Name': 'tag:key1', 'Value': ['value1']}])
        assert ret.response.snapshotSet is None

        ret = self.a1_r1.fcu.DescribeSnapshots(Filter=[{'Name': 'tag:key1', 'Value': ['value2']}])
        assert len(ret.response.snapshotSet) == 1

        ret = self.a1_r1.fcu.DescribeSnapshots(Filter=[{'Name': 'tag:key1', 'Value': ['value2', 'value3']}])
        assert len(ret.response.snapshotSet) == 2

        ret = self.a1_r1.fcu.DescribeSnapshots(Filter=[{'Name': 'tag-key', 'Value': ['key']}])
        assert ret.response.snapshotSet is None

        ret = self.a1_r1.fcu.DescribeSnapshots(Filter=[{'Name': 'tag-key', 'Value': ['key1']}])
        assert len(ret.response.snapshotSet) == 2

        ret = self.a1_r1.fcu.DescribeSnapshots(Filter=[{'Name': 'tag-key', 'Value': ['key1', 'key2']}])
        assert len(ret.response.snapshotSet) == 3

        ret = self.a1_r1.fcu.DescribeSnapshots(Filter=[{'Name': 'tag-value', 'Value': ['value']}])
        assert ret.response.snapshotSet is None

        ret = self.a1_r1.fcu.DescribeSnapshots(Filter=[{'Name': 'tag-value', 'Value': ['value1']}])
        assert len(ret.response.snapshotSet) == 2

        ret = self.a1_r1.fcu.DescribeSnapshots(Filter=[{'Name': 'tag-value', 'Value': ['value1', 'value2']}])
        assert len(ret.response.snapshotSet) == 3

        ret = self.a1_r1.fcu.DescribeSnapshots(Filter=[{'Name': 'tag:key1', 'Value': ['value2']}, {'Name': 'tag:key2', 'Value': ['value']}])
        assert ret.response.snapshotSet is None

        ret = self.a1_r1.fcu.DescribeSnapshots(Filter=[{'Name': 'tag:key1', 'Value': ['value2']}, {'Name': 'tag:key2', 'Value': ['value3']}])
        assert len(ret.response.snapshotSet) == 1

        ret = self.a1_r1.fcu.DescribeSnapshots(Filter=[{'Name': 'tag:key1', 'Value': ['value2', 'value3']},
                                                       {'Name': 'tag:key3', 'Value': ['value1', 'value2']}])
        assert len(ret.response.snapshotSet) == 1
