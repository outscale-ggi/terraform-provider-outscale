from qa_tina_tools.test_base import OscTinaTest


class Test_find(OscTinaTest):

    def test_T5840_without_devices_in_response(self):
        ret = self.a1_r1.intel.cluster.find(pz="in1", export_format="simple")
        for cluster in ret.response.result:
            assert not hasattr(cluster, 'devices')
