
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_tina_tools.test_base import OscTinaTest


class Test_add_group_member(OscTinaTest):

    @pytest.mark.region_gpu
    def test_T4310_invalid_servers(self):
        try:
            ret = self.a1_r1.intel.hardware.get_groups()
            selected_hwgrp = None
            for hwgrp in ret.response.result:
                if hwgrp.members:
                    selected_hwgrp = hwgrp
                    break
            if not selected_hwgrp:
                pytest.skip('Could not find hardware group')
            self.a1_r1.intel.hardware.add_group_member(group=selected_hwgrp.name, servers=['xx'])
        except OscApiException as err:
            assert_error(err, 200, 0, 'no-such-device')

    def test_T4311_invalid_group(self):
        try:
            self.a1_r1.intel.hardware.add_group_member(group='xx', servers=['xx'])
        except OscApiException as err:
            assert_error(err, 200, 0, 'no-such-servergroup')
