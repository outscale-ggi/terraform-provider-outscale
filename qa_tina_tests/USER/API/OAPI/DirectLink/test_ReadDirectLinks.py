
from qa_tina_tools.test_base import OscTinaTest


class Test_ReadDirectLinks(OscTinaTest):

    def test_T3904_empty_filters(self):
        ret = self.a1_r1.oapi.ReadDirectLinks().response.DirectLinks
        assert len(ret) == 0

    def test_T3905_filters_direct_link_ids(self):
        ret = self.a1_r1.oapi.ReadDirectLinks(Filters={'DirectLinkIds': ['dxcon-12345678']}).response.DirectLinks
        assert len(ret) == 0
