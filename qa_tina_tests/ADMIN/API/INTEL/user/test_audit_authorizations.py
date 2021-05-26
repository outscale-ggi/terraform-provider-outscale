from qa_test_tools.test_base import OscTestSuite, known_error


class Test_audit_authorizations(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_audit_authorizations, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_audit_authorizations, cls).teardown_class()

    def test_T5347_valid_use_case(self):
        ret = self.a1_r1.intel.user.audit_authorizations()
        assert len(ret.response.result.attach_all_sg) >= 1
        assert len(ret.response.result.allocate_everywhere) >= 1
        assert len(ret.response.result.use_dedicated_owner) >= 1
        assert len(ret.response.result.use_internal_instance_types) >= 1
        if len(ret.response.result.attach_all_nics) == 0:
            known_error('OPS-13703', 'ows.internal does not have attach_all_nics rights')
        assert False, 'Remove known error code'
        assert len(ret.response.result.attach_all_nics) >= 1
