
from qa_test_tools.test_base import OscTestSuite


class Test_read_flexible_gpu_catalog(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_read_flexible_gpu_catalog, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_read_flexible_gpu_catalog, cls).teardown_class()

    def test_T4404_with_session(self):
        ret = self.a1_r1.intel.pci.read_flexible_gpu_catalog()
        assert ret.response.result.flexible_gpu_catalog
