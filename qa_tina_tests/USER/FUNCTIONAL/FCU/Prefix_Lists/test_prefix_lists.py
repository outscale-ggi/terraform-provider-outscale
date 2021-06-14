from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.config import config_constants


SERVICES = ["fcu", "icu", "api", "eim", "lbu", "directlink"]
OPTIONAL_SERVICES = ["kms", "osu", "oos"]

class Test_prefix_lists(OscTestSuite):

    def test_T5716_content(self):
        self.a1_r1.fcu.DescribePrefixLists().response
        for service in SERVICES:
            assert "{}.{}".format(self.a1_r1.config.region.get_info(config_constants.HOST).split('.').reverse(),
                                  service)
        features = [feature.value for feature in self.a1_r1.config.region.get_info(config_constants.FEATURES)]
        for service in OPTIONAL_SERVICES:
            if service in features:
                assert "{}.{}".format(self.a1_r1.config.region.get_info(config_constants.HOST).split('.').reverse(),
                                      service)
