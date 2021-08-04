from qa_tina_tools.test_base import OscTinaTest


class Test_find(OscTinaTest):

    def test_T4000_with_type(self):
        self.a1_r1.intel.pci.find(type='gpu')
