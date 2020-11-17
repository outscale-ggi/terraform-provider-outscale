from qa_test_tools.test_base import OscTestSuite
import pytest


@pytest.mark.region_qa
class Test_get_slot_history(OscTestSuite):

    def test_T5340_without_dates(self):
        server_name = self.a1_r1.intel.hardware.get_servers().response.result[0].name
        self.a1_r1.intel.monitor.slot_history(what=server_name)
