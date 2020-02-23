# pylint: disable=missing-docstring

from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import assert_error
from qa_common_tools.test_base import OscTestSuite, known_error


class Test_DescribeProductTypes(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeProductTypes, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeProductTypes, cls).teardown_class()

    def test_T3484_no_params(self):
        ret = self.a1_r1.fcu.DescribeProductTypes()
        assert len(ret.response.productTypeSet) >= 5
        for product in ret.response.productTypeSet:
            assert product.productTypeId
            assert product.description

    def test_T3485_with_filter_product_type(self):
        try:
            ret = self.a1_r1.fcu.DescribeProductTypes(Filter=[{'Name': 'productTypeSet', 'Value': ['0001']}])
            assert False, 'Remove known error'
            assert len(ret.response.productTypeSet) == 1
            assert ret.response.productTypeSet[0].productTypeId == '0001'
        except OscApiException as error:
            if error.error_code == 'InvalidFilter':
                known_error('TINA-4870', "DescribeProductTypes: filter issue")
            assert False, 'Remove known error'

    def test_T3486_with_filter_invalid_product_type(self):
        try:
            ret = self.a1_r1.fcu.DescribeProductTypes(Filter=[{'Name': 'productTypeSet', 'Value': ['foo']}])
            assert False, 'Remove known error'
            assert not ret.response.productTypeSet
        except OscApiException as error:
            if error.error_code == 'InvalidFilter':
                known_error('TINA-4870', "DescribeProductTypes: filter issue")
            assert False, 'Remove known error'

    def test_T3487_with_invalid_filter(self):
        try:
            self.a1_r1.fcu.DescribeProductTypes(Filter=[{'Name': 'foo', 'Value': ['bar']}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidFilter', "The filter 'foo' is invalid")
