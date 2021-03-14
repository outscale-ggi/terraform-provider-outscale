
from qa_test_tools.test_base import OscTestSuite


class Test_ReadDirectLinkInterfaces(OscTestSuite):

    def test_T3914_empty_filters(self):
        ret = self.a1_r1.oapi.ReadDirectLinkInterfaces().response.DirectLinkInterfaces
        assert len(ret) == 0

    def test_T3915_filters_direct_link_ids(self):
        ret = self.a1_r1.oapi.ReadDirectLinkInterfaces(Filters={'DirectLinkIds': ['dxcon-12345678']}).response.DirectLinkInterfaces
        assert len(ret) == 0

    def test_T3916_filters_direct_link_interface_ids(self):
        ret = self.a1_r1.oapi.ReadDirectLinkInterfaces(Filters={'DirectLinkInterfaceIds': ['dxvif-12345678']}).response.DirectLinkInterfaces
        assert len(ret) == 0
