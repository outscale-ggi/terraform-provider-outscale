
import pytest

from qa_common_tools.test_base import OscTestSuite, is_skipped
from qa_common_tools.config.region import REGIONS_QA


class Test_get_all(OscTestSuite):

    @pytest.mark.skipif(**is_skipped(regions=REGIONS_QA, typ='QA'))
    def test_T1577_without_param(self):
        expected = ['dv-west-1', 'dv-west-2', 'dv-west-3', 'in-west-1', 'in-west-2']
        ret = self.a1_r1.intel.regions.get_all()
        actual = [region.name for region in ret.response.result]
        assert not set(actual).difference(set(expected))
        for region in ret.response.result:
            assert region.name in expected
            if region.name == self.a1_r1.config.region.name:
                assert region.current
            else:
                assert not region.current
