from qa_tina_tools.test_base import OscTinaTest


class Test_ReadPublicIpRanges(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_ReadPublicIpRanges, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ReadPublicIpRanges, cls).teardown_class()

    def test_T3676_empty_filters(self):
        ret = self.a1_r1.oapi.ReadPublicIpRanges().response.PublicIps
        assert len(ret) > 0
