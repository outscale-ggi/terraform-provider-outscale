

from qa_tina_tools.test_base import OscTinaTest


class Test_ReadLocations(OscTinaTest):

    def test_T3880_valid_case(self):
        ret = self.a1_r1.oapi.ReadLocations().response.Locations
        for location in ret:
            assert hasattr(location, 'Code')
            assert hasattr(location, 'Name')
