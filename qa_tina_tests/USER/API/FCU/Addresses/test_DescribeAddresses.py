

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error

NUM_ADDR = 3


class Test_DescribeAddresses(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeAddresses, cls).setup_class()
        cls.a1_eips = []
        try:
            for _ in range(NUM_ADDR):
                cls.a1_eips.append(cls.a1_r1.fcu.AllocateAddress(Domain='vpc').response)
            cls.eips_addr = [eip.publicIp for eip in cls.a1_eips]
            cls.a1_r1.fcu.CreateTags(ResourceId=[cls.a1_eips[0].allocationId], Tag=[{'Key': 'toto', 'Value': 'tata'}])
            cls.a1_r1.fcu.CreateTags(ResourceId=[cls.a1_eips[1].allocationId], Tag=[{'Key': 'tata', 'Value': 'toto'}])
            cls.a1_r1.fcu.CreateTags(ResourceId=[cls.a1_eips[2].allocationId], Tag=[{'Key': 'tata', 'Value': 'tutu'}])
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.a1_eips:
                for eip in cls.a1_eips:
                    cls.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)
        finally:
            super(Test_DescribeAddresses, cls).teardown_class()

    def test_T3085_with_other_account(self):
        ret = self.a2_r1.fcu.DescribeAddresses().response.addressesSet
        assert not ret, 'Unexpected non-empty result'

    def test_T3084_no_param(self):
        ret = self.a1_r1.fcu.DescribeAddresses().response.addressesSet
        assert len({addr.publicIp for addr in ret}) == len(self.a1_eips)
        for addr in ret:
            assert addr.publicIp in self.eips_addr

    def test_T3242_with_other_account_with_param(self):
        try:
            self.a2_r1.fcu.DescribeAddresses(PublicIp=self.eips_addr)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidAddress.NotFound', None)
            assert error.message.startswith('Address not found: ')
            msg_addrs = set(error.message[len('Address not found: '):].split(', '))
            assert len(msg_addrs) == len(self.eips_addr)
            for addr in msg_addrs:
                assert addr in self.eips_addr

    def test_T3243_with_other_account_with_filter(self):
        ret = self.a2_r1.fcu.DescribeAddresses(Filter=[{'Name': 'public-ip', 'Value': self.eips_addr}])
        assert not ret.response.addressesSet

    def test_T4003_valid_filter_by_tag_key(self):
        try:
            self.a1_r1.fcu.DescribeAddresses(Filter=[{'Name': 'tag-key', 'Value': 'tata'}])
            known_error('TINA-5164', "Call should not have been successful")
        except OscApiException as error:
            assert_error(error, 400, '', '')

    def test_T4004_valid_filter_by_tag_value(self):
        try:
            self.a1_r1.fcu.DescribeAddresses(Filter=[{'Name': 'tag-value', 'Value': 'toto'}])
            known_error('TINA-5164', "Call should not have been successful")
        except OscApiException as error:
            assert_error(error, 400, '', '')

    def test_T4005_valid_filter_by_tag_key_and_value(self):
        try:
            self.a1_r1.fcu.DescribeAddresses(Filter=[{'Name': 'tag:toto', 'Value': 'tata'}])
            known_error('TINA-5164', "Call should not have been successful")
        except OscApiException as error:
            assert_error(error, 400, '', '')
