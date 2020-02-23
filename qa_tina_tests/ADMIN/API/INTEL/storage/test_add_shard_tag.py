from qa_common_tools.test_base import OscTestSuite


class Test_add_shard_tag(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.mount_points = []
        super(Test_add_shard_tag, cls).setup_class()
        try:
            ret = cls.a1_r1.intel.storage.find_shards()
            cls.mount_points = [res.mount_point for res in ret.response.result]
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        super(Test_add_shard_tag, cls).teardown_class()

    def test_T3757_valid_params(self):
        ret = None
        try:
            ret = self.a1_r1.intel.storage.add_shard_tag(mount_point=self.mount_points[0], tag='tag', value='value')
        finally:
            if ret:
                self.a1_r1.intel.storage.delete_shard_tag(mount_point=self.mount_points[0], tag='tag')

    def test_T3758_with_overwrite(self):
        ret = None
        try:
            ret = self.a1_r1.intel.storage.add_shard_tag(mount_point=self.mount_points[0], tag='tag', value='value')
            self.a1_r1.intel.storage.add_shard_tag(mount_point=self.mount_points[0], tag='tag', value='value1', overwrite=True)
            shard = self.a1_r1.intel.storage.find_shards(mount_point=self.mount_points[0]).response.result[0]
            for tag in shard.tags:
                if tag.key == 'tag':
                    assert tag.value == 'value1'
        finally:
            if ret:
                self.a1_r1.intel.storage.delete_shard_tag(mount_point=self.mount_points[0], tag='tag')
