import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools import misc
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_customer_gateways
from qa_tina_tools.tools.tina.create_tools import create_customer_gateway
from qa_tina_tools.tools.tina.wait_tools import wait_customer_gateways_state


class Test_DescribeCustomerGateways(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeCustomerGateways, cls).setup_class()
        cls.cgw_ip = Configuration.get('ipaddress', 'cgw_ip')
        try:
            cls.id_list_account1 = []
            cls.ip_list_account1 = []
            cls.id_account2 = []
            for i in range(3):
                ret = create_customer_gateway(cls.a1_r1, bgp_asn=12, ip_address='46.22%s.147.8' % i, typ='ipsec.1')
                wait_customer_gateways_state(cls.a1_r1, [ret.response.customerGateway.customerGatewayId], state='available')
                assert ret.response.customerGateway.bgpAsn == '12'
                assert ret.response.customerGateway.ipAddress == '46.22%s.147.8' % i
                assert ret.response.customerGateway.state == 'available'
                cls.id_list_account1.append(ret.response.customerGateway.customerGatewayId)
                cls.ip_list_account1.append(ret.response.customerGateway.ipAddress)  
            for conn in [cls.a1_r1, cls.a2_r1]:
                ret = create_customer_gateway(conn, bgp_asn=12, ip_address=cls.cgw_ip, typ='ipsec.1')
                wait_customer_gateways_state(conn, [ret.response.customerGateway.customerGatewayId], state='available')
                assert ret.response.customerGateway.bgpAsn == '12'
                assert ret.response.customerGateway.ipAddress == cls.cgw_ip
                assert ret.response.customerGateway.state == 'available'
                if conn == cls.a1_r1:
                    cls.id_list_account1.append(ret.response.customerGateway.customerGatewayId)
                    cls.ip_list_account1.append(ret.response.customerGateway.ipAddress)
                else:
                    cls.id_account2 = ret.response.customerGateway.customerGatewayId
        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            cleanup_customer_gateways(cls.a1_r1)
            cleanup_customer_gateways(cls.a2_r1)
        finally:
            super(Test_DescribeCustomerGateways, cls).teardown_class()

    def test_T775_without_param(self):
        ret = self.a1_r1.fcu.DescribeCustomerGateways()
        for i in range(len(ret.response.customerGatewaySet)):
            if ret.response.customerGatewaySet[i].state == 'available':
                assert ret.response.customerGatewaySet[i].bgpAsn == '12'
                assert ret.response.customerGatewaySet[i].ipAddress in self.ip_list_account1

    def test_T776_with_valid_filter(self):
        ret = self.a1_r1.fcu.DescribeCustomerGateways(Filter=[{'Name': 'state', 'Value': 'available'}])
        assert len(ret.response.customerGatewaySet) == 4
        ret = self.a1_r1.fcu.DescribeCustomerGateways(Filter=[{'Name': 'customer-gateway-id', 'Value': self.id_list_account1[3]}])
        assert len(ret.response.customerGatewaySet) == 1
        ret = self.a1_r1.fcu.DescribeCustomerGateways(Filter=[{'Name': 'ip-address', 'Value': self.ip_list_account1[1]}])
        assert len(ret.response.customerGatewaySet) >= 1
        ret = self.a1_r1.fcu.DescribeCustomerGateways(Filter=[{'Name': 'bgp-asn', 'Value': 12}])
        assert len(ret.response.customerGatewaySet) >= 1
        ret = self.a1_r1.fcu.DescribeCustomerGateways(Filter=[{'Name': 'type', 'Value': 'ipsec.1'}])
        assert len(ret.response.customerGatewaySet) >= 1
        ret = self.a1_r1.fcu.DescribeCustomerGateways(Filter=[{'Name': 'customer-gateway-id', 'Value': [self.id_list_account1[0],
                                                                                                           self.id_list_account1[1]]}])
        assert len(ret.response.customerGatewaySet) == 2
        ret = self.a1_r1.fcu.DescribeCustomerGateways(Filter=[{'Name': 'ip-address', 'Value': self.ip_list_account1[1]},
                                                                 {'Name': 'customer-gateway-id', 'Value': self.id_list_account1[1]}])
        assert len(ret.response.customerGatewaySet) == 1

    def test_T777_with_invalid_filter_ip_address(self):
        ret = self.a1_r1.fcu.DescribeCustomerGateways(Filter=[{'Name': 'ip-address', 'Value': 'foo'}])
        assert ret.response.customerGatewaySet is None

    def test_T1793_with_invalid_filter_type(self):
        ret = self.a1_r1.fcu.DescribeCustomerGateways(Filter=[{'Name': 'type', 'Value': 'foo'}])
        assert ret.response.customerGatewaySet is None

    def test_T1794_with_invalid_filter_bgp_asn(self):
        ret = self.a1_r1.fcu.DescribeCustomerGateways(Filter=[{'Name': 'bgp-asn', 'Value': 'foo'}])
        assert ret.response.customerGatewaySet is None

    def test_T1795_with_invalid_filter_cgw_id(self):
        ret = self.a1_r1.fcu.DescribeCustomerGateways(Filter=[{'Name': 'customer-gateway-id', 'Value': 'foo'}])
        assert ret.response.customerGatewaySet is None

    def test_T1796_with_invalid_filter_tag_key(self):
        ret = self.a1_r1.fcu.DescribeCustomerGateways(Filter=[{'Name': 'tag-key', 'Value': 'foo'}])
        assert ret.response.customerGatewaySet is None

    def test_T1797_with_invalid_filter_tag_value(self):
        ret = self.a1_r1.fcu.DescribeCustomerGateways(Filter=[{'Name': 'tag-value', 'Value': 'foo'}])
        assert ret.response.customerGatewaySet is None

    def test_T1798_with_invalid_filter_state(self):
        ret = self.a1_r1.fcu.DescribeCustomerGateways(Filter=[{'Name': 'state', 'Value': 'foo'}])
        assert ret.response.customerGatewaySet is None

    def test_T778_with_valid_cgw_id(self):
        self.a1_r1.fcu.DescribeCustomerGateways(CustomerGatewayId=self.id_list_account1[0])
        self.a1_r1.fcu.DescribeCustomerGateways(CustomerGatewayId=[self.id_list_account1[0], self.id_list_account1[1]])

    def test_T779_with_invalid_cgw_id(self):
        try:
            self.a1_r1.fcu.DescribeCustomerGateways(CustomerGatewayId='toto')
            pytest.fail('Call should not have been successful, invalid id')
        except OscApiException as error:
            misc.assert_error(error, 400, 'InvalidCustomerGatewayID.NotFound', "The customerGateway ID 'toto' does not exist")
        try:
            self.a1_r1.fcu.DescribeCustomerGateways(CustomerGatewayId='cwg-xxxxxxxx')
            pytest.fail('Call should not have been successful, invalid id')
        except OscApiException as error:
            misc.assert_error(error, 400, "InvalidCustomerGatewayID.NotFound", "The customerGateway ID 'cwg-xxxxxxxx' does not exist")
        try:
            name = self.id_list_account1[0].replace('cgw-', 'cgw-xxx')
            self.a1_r1.fcu.DescribeCustomerGateways(CustomerGatewayId=name)
            pytest.fail('Call should not have been successful, invalid id')
        except OscApiException as error:
            misc.assert_error(error, 400, "InvalidCustomerGatewayID.NotFound", "The customerGateway ID '{}' does not exist".format(name))

    def test_T780_with_other_account_cgw_id(self):
        try:
            self.a1_r1.fcu.DescribeCustomerGateways(CustomerGatewayId=[self.id_account2])
            pytest.fail('Call should not have been successful, id from another account')
        except OscApiException as error:
            misc.assert_error(error, 400, 'InvalidCustomerGatewayID.NotFound',
                              "The customerGateway ID '{}' does not exist".format(self.id_account2))

    def test_T781_with_valid_filter_and_cgw_id(self):
        self.a1_r1.fcu.DescribeCustomerGateways(CustomerGatewayId=self.id_list_account1[0], Filter=[{'Name': 'state',
                                                                                                        'Value': 'available'}])

    def test_T5954_with_tag_filter(self):
        misc.execute_tag_tests(self.a1_r1, 'CustomerGateway', self.id_list_account1,
                               'fcu.DescribeCustomerGateways', 'customerGatewaySet.customerGatewayId')
