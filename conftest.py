import pytest

from qa_test_tools.config import config_constants as constants
from qa_test_tools.config import OscAZ
from qa_test_tools.test_base import get_export_value


def pytest_runtest_setup(item):

    # cur_region --> list supported feature
    cur_region = OscAZ(az_name=get_export_value('OSC_AZS').split(" ")[0])
    cur_region_features = [feature.value for feature in cur_region.get_info(constants.FEATURES)]
    cur_region_features_tickets = []
    try:
        cur_region_features_tickets = cur_region.get_info(constants.FEATURES_TICKETS)
    except ValueError:
        pass

    # cur_test --> list needed feature
    cur_test_features = [mark.name for mark in item.iter_markers() if 'region_' in mark.name]

    # skip test without marker
    if not cur_test_features and get_export_value('OSC_SKIP_DEFAULT'):
        pytest.skip("Skip tests without feature requirements")

    # all test needed features must be available in current region
    for test_feature in cur_test_features:
        if test_feature == 'region_storageservice':
            if 'osu' in cur_region_features or 'oos' in cur_region_features:
                assert cur_region.get_info(constants.STORAGESERVICE).value in cur_region_features
                continue
        feature = test_feature[len("region_"):]
        if test_feature.startswith("region_") and feature not in cur_region_features:
            if cur_region_features_tickets and feature in cur_region_features_tickets and cur_region_features_tickets[feature] is not None:
                pytest.skip("Test requires feature '{}', not available on {} --> {}".format(feature, cur_region.name,
                                                                                            cur_region_features_tickets[feature]))
            else:
                pytest.skip("Test requires feature '{}', not available on {}".format(feature, cur_region.name))
