# pylint: disable=missing-docstring

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_DescribeInstanceTypes(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeInstanceTypes, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeInstanceTypes, cls).teardown_class()

    def test_T3494_no_params(self):
        ret = self.a1_r1.fcu.DescribeInstanceTypes()
        # assert len(ret.response.instanceTypeSet) >= 111
        for inst in ret.response.instanceTypeSet:
            assert hasattr(inst, 'name')
            assert hasattr(inst, 'vcpu')
            assert hasattr(inst, 'memory')
            assert hasattr(inst, 'storageCount')
            assert hasattr(inst, 'maxIpAddresses')
            assert hasattr(inst, 'ebsOptimizedAvailable')
            # assert hasattr(inst, 'ephemeralsType')
            # assert hasattr(inst, 'gpu')

    def test_T3495_with_filter_name(self):
        ret = self.a1_r1.fcu.DescribeInstanceTypes(Filter=[{'Name': 'name', 'Value': ['t2.nano']}])
        assert len(ret.response.instanceTypeSet) == 1
        assert ret.response.instanceTypeSet[0].name == 't2.nano'

    def test_T3496_with_filter_vcpu(self):
        ret = self.a1_r1.fcu.DescribeInstanceTypes(Filter=[{'Name': 'vcpu', 'Value': ['1']}])
        assert len(ret.response.instanceTypeSet) >= 9
        for inst in ret.response.instanceTypeSet:
            assert inst.vcpu == '1'

    def test_T3497_with_filter_memory(self):
        ret = self.a1_r1.fcu.DescribeInstanceTypes(Filter=[{'Name': 'memory', 'Value': ['1073741824']}])
        assert len(ret.response.instanceTypeSet) >= 1
        for inst in ret.response.instanceTypeSet:
            assert inst.memory == '1073741824'

    def test_T3498_with_filter_storage_size(self):
        ret = self.a1_r1.fcu.DescribeInstanceTypes(Filter=[{'Name': 'storage-size', 'Value': ['17179869184']}])
        assert len(ret.response.instanceTypeSet) == 1
        assert ret.response.instanceTypeSet[0].storageSize == '17179869184'

    def test_T3499_with_filter_storage_count(self):
        ret = self.a1_r1.fcu.DescribeInstanceTypes(Filter=[{'Name': 'storage-count', 'Value': ['1']}])
        assert len(ret.response.instanceTypeSet) >= 31
        for inst in ret.response.instanceTypeSet:
            assert inst.storageCount == '1'

    def test_T3500_with_filter_ebs_optimized(self):
        ret = self.a1_r1.fcu.DescribeInstanceTypes(Filter=[{'Name': 'ebs-optimized-available', 'Value': ['true']}])
        assert len(ret.response.instanceTypeSet) >= 62
        for inst in ret.response.instanceTypeSet:
            assert inst.ebsOptimizedAvailable == 'true'

    def test_T3501_with_filter_invalid_name(self):
        ret = self.a1_r1.fcu.DescribeInstanceTypes(Filter=[{'Name': 'name', 'Value': ['foo']}])
        assert not ret.response.instanceTypeSet

    def test_T3502_with_filter_invalid_vcpu(self):
        ret = self.a1_r1.fcu.DescribeInstanceTypes(Filter=[{'Name': 'vcpu', 'Value': ['foo']}])
        assert not ret.response.instanceTypeSet

    def test_T3503_with_filter_invalid_memory(self):
        ret = self.a1_r1.fcu.DescribeInstanceTypes(Filter=[{'Name': 'memory', 'Value': ['foo']}])
        assert not ret.response.instanceTypeSet

    def test_T3504_with_filter_invalid_storage_size(self):
        ret = self.a1_r1.fcu.DescribeInstanceTypes(Filter=[{'Name': 'storage-size', 'Value': ['foo']}])
        assert not ret.response.instanceTypeSet

    def test_T3505_with_filter_invalid_storage_count(self):
        ret = self.a1_r1.fcu.DescribeInstanceTypes(Filter=[{'Name': 'storage-count', 'Value': ['foo']}])
        assert not ret.response.instanceTypeSet

    def test_T3506_with_filter_invalid_ebs_optimized(self):
        ret = self.a1_r1.fcu.DescribeInstanceTypes(Filter=[{'Name': 'ebs-optimized-available', 'Value': ['foo']}])
        assert not ret.response.instanceTypeSet

    def test_T3507_with_invalid_filter(self):
        try:
            self.a1_r1.fcu.DescribeInstanceTypes(Filter=[{'Name': 'foo', 'Value': ['bar']}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidFilter', "The filter 'foo' is invalid")
