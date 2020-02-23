from qa_common_tools.test_base import OscTestSuite

class Test_find(OscTestSuite):

    def test_T4000_with_type(self):
        self.a1_r1.intel.pci.find(type='gpu')
