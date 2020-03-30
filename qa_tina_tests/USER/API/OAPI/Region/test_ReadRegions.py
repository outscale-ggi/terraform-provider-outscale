from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import assert_dry_run


class Test_ReadRegions(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadRegions, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ReadRegions, cls).teardown_class()

    def verify_response(self, response):
        for reg in response.Regions:
            assert hasattr(reg, 'RegionName'), "Missing attribute 'regionName' in response"
            assert hasattr(reg, 'Endpoint'), "Missing attribute 'regionEndpoint' in response"
        assert len(response.Regions) == len(set([reg.RegionName for reg in response.Regions])), "Duplicate(s) in region names"
        assert len(response.Regions) == len(set([reg.Endpoint for reg in response.Regions])), 'Duplicate(s) in region endpoints'

    def test_T4768_without_params(self):
        resp = self.a1_r1.oapi.ReadRegions().response
        self.verify_response(resp)

    def test_T4769_dry_run(self):
        ret = self.a1_r1.oapi.ReadSubregions(DryRun=True)
        assert_dry_run(ret)
