# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

from qa_common_tools.test_base import OscTestSuite


class Test_DescribeVirtualGateways(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeVirtualGateways, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeVirtualGateways, cls).teardown_class()

    def test_T1912_without_param(self):
        ret = self.a1_r1.directlink.DescribeVirtualGateways()
        assert isinstance(ret.response.virtualGateways, list)
        assert not ret.response.virtualGateways
