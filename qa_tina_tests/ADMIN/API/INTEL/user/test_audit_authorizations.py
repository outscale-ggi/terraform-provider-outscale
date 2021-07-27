
import pytest
from qa_tina_tools.test_base import OscTinaTest
from qa_test_tools.config import config_constants
from qa_test_tools.config.region import Feature


@pytest.mark.region_admin
class Test_audit_authorizations(OscTinaTest):

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
        if Feature.ODS in self.a1_r1.config.region.get_info(config_constants.FEATURES):
            assert len(ret.response.result.attach_all_nics) == 1
        else:
            assert len(ret.response.result.attach_all_nics) == 0
