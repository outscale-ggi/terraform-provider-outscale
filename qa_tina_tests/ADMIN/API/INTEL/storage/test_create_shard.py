from qa_test_tools.test_base import OscTestSuite


class Test_create_shard(OscTestSuite):

    def test_T5580_valid_params(self):
        ret = None
        try:
            ret = self.a1_r1.intel.storage.create_shard(path='/testqa', host='in2-filer-1in2-filer-1-piops', pz='in2')
            assert ret.response.result.tags[0].value == 'standard, gp2'
        finally:
            if ret:
                self.a1_r1.intel.storage.delete_shard(mount_point=ret.response.result.mount_point)