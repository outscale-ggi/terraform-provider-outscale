from qa_test_tools.test_base import OscTestSuite


class Test_ReadSubregions(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadSubregions, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ReadSubregions, cls).teardown_class()

    def verify_response(self, response):
        for reg in response:
            assert hasattr(reg, 'RegionName'), "Missing attribute 'RegionName' in response"
            assert hasattr(reg, 'SubregionName'), "Missing attribute 'SubregionName' in response"
            assert hasattr(reg, 'State'), "Missing attribute 'State' in response"

    def test_T3711_empty_filters(self):
        ret = self.a1_r1.oapi.ReadSubregions().response.Subregions
        assert len(ret)
        self.verify_response(ret)

    def test_T3714_filters_invalid_subregion_names(self):
        ret = self.a1_r1.oapi.ReadSubregions(Filters={'SubregionNames': ['toto']}).response.Subregions
        assert len(ret) == 0
        
    def test_T3715_filters_current_subregion_names(self):
        ret = self.a1_r1.oapi.ReadSubregions(Filters={'SubregionNames': [self.a1_r1.config.region.az_name]}).response.Subregions
        assert len(ret) == 1
        for subregion in ret:
            assert subregion.SubregionName == self.a1_r1.config.region.az_name
