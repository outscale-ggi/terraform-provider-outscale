# -*- coding:utf-8 -*-
from qa_common_tools.test_base import OscTestSuite


class Test_ReadProductTypes(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadProductTypes, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ReadProductTypes, cls).teardown_class()

    def test_T3660_empty_filters(self):
        ret = self.a1_r1.oapi.ReadProductTypes().response.ProductTypes
        assert len(ret) > 0
        for product in ret:
            assert product.ProductTypeId
            assert product.Description

    def test_T3661_with_filter_product_types(self):
        ret = self.a1_r1.oapi.ReadProductTypes(Filters={'ProductTypeIds': ['0001']}).response.ProductTypes
        assert len(ret) == 1
        assert ret[0].ProductTypeId == '0001'

    def test_T3662_with_filter_invalid_product_types(self):
        ret = self.a1_r1.oapi.ReadProductTypes(Filters={'ProductTypeIds': ['foo']}).response.ProductTypes
        assert len(ret) == 0
