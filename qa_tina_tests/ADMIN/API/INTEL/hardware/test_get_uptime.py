from qa_tina_tools.test_base import OscTinaTest


class Test_get_uptime(OscTinaTest):

    def test_T3780_valid_params(self):
        ret = self.a1_r1.intel.hardware.get_servers()
        ret = self.a1_r1.intel.hardware.get_uptime(server=ret.response.result[0].name)
        assert ret.response.result > 0
