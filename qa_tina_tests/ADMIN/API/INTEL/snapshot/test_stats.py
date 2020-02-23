from qa_common_tools.test_base import OscTestSuite


class Test_stats(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_stats, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_stats, cls).teardown_class()

    def test_T3786_valid_params(self):
        ret = self.a1_r1.intel.snapshot.stats()
        assert hasattr(ret.response.result, 'completed')
        assert hasattr(ret.response.result, 'count')
        assert hasattr(ret.response.result, 'deleting')
        assert hasattr(ret.response.result, 'error')
        assert hasattr(ret.response.result, 'pending')
        assert hasattr(ret.response.result, 'importing')
        assert hasattr(ret.response.result, 'pending/queued')
