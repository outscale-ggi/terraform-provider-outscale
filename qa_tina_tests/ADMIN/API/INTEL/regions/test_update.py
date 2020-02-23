
from qa_common_tools.test_base import OscTestSuite


class Test_update(OscTestSuite):

    def test_T1578_without_param(self):
        self.a1_r1.intel.regions.update()
