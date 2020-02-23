
from qa_common_tools.test_base import OscTestSuite


class Test_current(OscTestSuite):

    def test_T1576_without_param(self):
        ret = self.a1_r1.intel.regions.current()
        assert ret.response.result.name == self.a1_r1.config.region.name
        assert ret.response.result.current
