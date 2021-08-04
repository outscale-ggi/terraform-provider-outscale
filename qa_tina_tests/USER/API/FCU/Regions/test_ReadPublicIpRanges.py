from qa_sdk_pub.osc_api import AuthMethod
from qa_tina_tools.test_base import OscTinaTest


class Test_ReadPublicIpRanges(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_ReadPublicIpRanges, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ReadPublicIpRanges, cls).teardown_class()

    def test_T2173_without_param(self):
        ret = self.a1_r1.fcu.ReadPublicIpRanges()
        assert len(ret.response.publicIpSet) > 0

    def test_T3579_without_authent(self):
        ret = self.a1_r1.fcu.ReadPublicIpRanges(auth=AuthMethod.Empty)
        assert len(ret.response.publicIpSet) > 0
