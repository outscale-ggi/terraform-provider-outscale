import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_customer_gateways
from qa_tina_tools.tools.tina.create_tools import create_customer_gateway
from qa_tina_tools.tools.tina.wait_tools import wait_customer_gateways_state


class Test_DescribeCustomerGateways(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeCustomerGateways, cls).setup_class()
        cls.cgw_ip = Configuration.get('ipaddress', 'cgw_ip')
        try:
            cls.id_list = []
            for i in range(2):
                ret = create_customer_gateway(cls.conns[0], bgp_asn=12, ip_address='46.22%s.147.8' % i, typ='ipsec.1')
                wait_customer_gateways_state(cls.conns[0], [ret.response.customerGateway.customerGatewayId], state='available')
                assert ret.response.customerGateway.bgpAsn == '12'
                assert ret.response.customerGateway.ipAddress == '46.22%s.147.8' % i
                assert ret.response.customerGateway.state == 'available'
                cls.id_list.append({'cg_id': ret.response.customerGateway.customerGatewayId, 'ip': ret.response.customerGateway.ipAddress})
            gateway_id_list = []
            for i in range(2):
                ret = create_customer_gateway(cls.conns[i], bgp_asn=12, ip_address=cls.cgw_ip, typ='ipsec.1')
                wait_customer_gateways_state(cls.conns[i], [ret.response.customerGateway.customerGatewayId], state='available')
                assert ret.status_code == 200, ret.response.display()
                assert ret.response.customerGateway.bgpAsn == '12'
                assert ret.response.customerGateway.ipAddress == cls.cgw_ip
                assert ret.response.customerGateway.state == 'available'
                gateway_id_list.append({'cg_id': ret.response.customerGateway.customerGatewayId, 'ip': ret.response.customerGateway.ipAddress})
            cls.id_list_account1 = [cls.id_list[0]['cg_id'], cls.id_list[1]['cg_id'], gateway_id_list[0]['cg_id']]
            cls.ip_list_account1 = [cls.id_list[0]['ip'], cls.id_list[1]['ip'], gateway_id_list[0]['ip']]
            cls.id_account2 = gateway_id_list[1]['cg_id']
            cls.conns[0].fcu.CreateTags(Tag=[{'Key': 'tag', 'Value': 'Hello'}], ResourceId=cls.id_list_account1[2])
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            cleanup_customer_gateways(cls.conns[0])
            cleanup_customer_gateways(cls.conns[1])
        finally:
            super(Test_DescribeCustomerGateways, cls).teardown_class()

    def test_T775_without_param(self):
        ret = self.conns[0].fcu.DescribeCustomerGateways()
        for i in range(len(ret.response.customerGatewaySet)):
            if ret.response.customerGatewaySet[i].state == 'available':
                assert ret.response.customerGatewaySet[i].bgpAsn == '12'
                assert ret.response.customerGatewaySet[i].ipAddress in self.ip_list_account1

    def test_T776_with_valid_filter(self):
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'state', 'Value': 'available'}])
        assert len(ret.response.customerGatewaySet) == 3
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'customer-gateway-id', 'Value': self.id_list_account1[2]}])
        assert len(ret.response.customerGatewaySet) == 1
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'ip-address', 'Value': self.ip_list_account1[1]}])
        assert len(ret.response.customerGatewaySet) >= 1
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'bgp-asn', 'Value': 12}])
        assert len(ret.response.customerGatewaySet) >= 1
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'type', 'Value': 'ipsec.1'}])
        assert len(ret.response.customerGatewaySet) >= 1
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'customer-gateway-id', 'Value': [self.id_list_account1[0],
                                                                                                           self.id_list_account1[1]]}])
        assert len(ret.response.customerGatewaySet) == 2
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'ip-address', 'Value': self.ip_list_account1[1]},
                                                                 {'Name': 'customer-gateway-id', 'Value': self.id_list_account1[1]}])
        assert len(ret.response.customerGatewaySet) == 1
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'tag:tag', 'Value': 'Hello'}])
        assert len(ret.response.customerGatewaySet) >= 1
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'tag-key', 'Value': 'tag'}])
        assert len(ret.response.customerGatewaySet) >= 1
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'tag-value', 'Value': 'Hello'}])
        assert len(ret.response.customerGatewaySet) >= 1

    def test_T777_with_invalid_filter_ip_address(self):
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'ip-address', 'Value': 'foo'}])
        assert ret.response.customerGatewaySet is None

    def test_T1793_with_invalid_filter_type(self):
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'type', 'Value': 'foo'}])
        assert ret.response.customerGatewaySet is None

    def test_T1794_with_invalid_filter_bgp_asn(self):
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'bgp-asn', 'Value': 'foo'}])
        assert ret.response.customerGatewaySet is None

    def test_T1795_with_invalid_filter_cgw_id(self):
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'customer-gateway-id', 'Value': 'foo'}])
        assert ret.response.customerGatewaySet is None

    def test_T1796_with_invalid_filter_tag_key(self):
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'tag-key', 'Value': 'foo'}])
        assert ret.response.customerGatewaySet is None

    def test_T1797_with_invalid_filter_tag_value(self):
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'tag-value', 'Value': 'foo'}])
        assert ret.response.customerGatewaySet is None

    def test_T1798_with_invalid_filter_state(self):
        ret = self.conns[0].fcu.DescribeCustomerGateways(Filter=[{'Name': 'state', 'Value': 'foo'}])
        assert ret.response.customerGatewaySet is None

    def test_T778_with_valid_cgw_id(self):
        self.conns[0].fcu.DescribeCustomerGateways(CustomerGatewayId=self.id_list_account1[0])
        self.conns[0].fcu.DescribeCustomerGateways(CustomerGatewayId=[self.id_list_account1[0], self.id_list_account1[1]])

    def test_T779_with_invalid_cgw_id(self):
        try:
            self.conns[0].fcu.DescribeCustomerGateways(CustomerGatewayId='toto')
            pytest.fail('Call should not have been successful, invalid id')
        except OscApiException as error:
            assert_error(error, 400, 'InvalidCustomerGatewayID.NotFound', "The customerGateway ID 'toto' does not exist")
        try:
            self.conns[0].fcu.DescribeCustomerGateways(CustomerGatewayId='cwg-xxxxxxxx')
            pytest.fail('Call should not have been successful, invalid id')
        except OscApiException as error:
            assert_error(error, 400, "InvalidCustomerGatewayID.NotFound", "The customerGateway ID 'cwg-xxxxxxxx' does not exist")
        try:
            name = self.id_list_account1[0].replace('cgw-', 'cgw-xxx')
            self.conns[0].fcu.DescribeCustomerGateways(CustomerGatewayId=name)
            pytest.fail('Call should not have been successful, invalid id')
        except OscApiException as error:
            assert_error(error, 400, "InvalidCustomerGatewayID.NotFound", "The customerGateway ID '{}' does not exist".format(name))

    def test_T780_with_other_account_cgw_id(self):
        try:
            self.conns[0].fcu.DescribeCustomerGateways(CustomerGatewayId=self.id_account2)
            pytest.fail('Call should not have been successful, id from another account')
        except OscApiException as error:
            assert_error(error, 400, 'InvalidCustomerGatewayID.NotFound', "The customerGateway ID '{}' does not exist".format(self.id_account2))

    def test_T781_with_valid_filter_and_cgw_id(self):
        self.conns[0].fcu.DescribeCustomerGateways(CustomerGatewayId=self.id_list_account1[0], Filter=[{'Name': 'state',
                                                                                                        'Value': 'available'}])
