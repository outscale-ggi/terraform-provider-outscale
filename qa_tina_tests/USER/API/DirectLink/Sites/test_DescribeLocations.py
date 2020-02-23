# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

import pytest
from qa_common_tools.test_base import OscTestSuite


@pytest.mark.region_directlink
class Test_DescribeLocations(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeLocations, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeLocations, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T1907_without_param(self):
        ret = self.a1_r1.directlink.DescribeLocations()
        assert isinstance(ret.response.locations, list)
        assert hasattr(ret.response, 'locations')
