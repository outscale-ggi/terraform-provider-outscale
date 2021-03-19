

from qa_test_tools.test_base import OscTestSuite


class Test_ReadLocations(OscTestSuite):

    def test_T3880_valid_case(self):
        ret = self.a1_r1.oapi.ReadLocations().response.Locations
        for location in ret:
            assert hasattr(location, 'Code')
            assert hasattr(location, 'Name')
