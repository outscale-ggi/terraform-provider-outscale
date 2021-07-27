
import pytest
from qa_tina_tools.test_base import OscTinaTest


@pytest.mark.region_admin
class Test_create_shard(OscTinaTest):

    def test_T5580_valid_params(self):
        if self.a1_r1.config.region.name != "in-west-1":
            pytest.skip('Only region in-west-1 has been configured')
        ret = None
        try:
            ret = self.a1_r1.intel.storage.create_shard(path='/testqa', host='some_host', pz='in1')
            assert ret.response.result.tags[0].value == 'standard, gp2'
        finally:
            if ret:
                self.a1_r1.intel.storage.delete_shard(mount_point=ret.response.result.mount_point)
