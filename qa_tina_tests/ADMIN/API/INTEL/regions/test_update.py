
from qa_tina_tools.test_base import OscTinaTest


class Test_update(OscTinaTest):

    def test_T1578_without_param(self):
        self.a1_r1.intel.regions.update()
