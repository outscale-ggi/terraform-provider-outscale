from qa_test_tools.config.configuration import Configuration
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_customer_gateways
from qa_tina_tools.tools.tina.create_tools import create_customer_gateway
from qa_tina_tools.tools.tina.wait_tools import wait_customer_gateways_state


class Test_CreateCustomerGateway(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateCustomerGateway, cls).setup_class()
        cls.cgw_ip = Configuration.get('ipaddress', 'cgw_ip')

    def teardown_method(self, method):
        try:
            cleanup_customer_gateways(self.a1_r1)
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T1274_missing_arg_type(self):
        try:
            create_customer_gateway(self.a1_r1, bgp_asn=12, ip_address=self.cgw_ip)
            assert False, 'Call should not have been successful, bad number of arguments'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: Type')

    def test_T759_missing_arg_ip_address(self):
        try:
            create_customer_gateway(self.a1_r1, bgp_asn=12, typ='standard')
            assert False, 'Call should not have been successful, bad number of arguments'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Value of parameter 'Type' is not valid: standard. Supported values: ipsec.1")

    def test_T1273_missing_arg_bgp_asn(self):
        create_customer_gateway(self.a1_r1, ip_address=self.cgw_ip, typ='ipsec.1')

    def test_T760_invalid_ip_address(self):
        try:
            create_customer_gateway(self.a1_r1, bgp_asn=12, ip_address='462311478', typ='ipsec.1')
            assert False, 'Call should not have been successful, invalid ip address'
        except OscApiException as error: 
            assert_error(error, 400, 'InvalidParameterValue', 'Invalid IPv4 address: 462311478')

    def test_T761_invalid_type(self):
        try:
            create_customer_gateway(self.a1_r1, bgp_asn=12, ip_address=self.cgw_ip, typ='standard')
            assert False, 'Call should not have been successful, invalid type'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Value of parameter 'Type' is not valid: standard. Supported values: ipsec.1")

    def test_T762_all_valid_param(self):
        ret = create_customer_gateway(self.a1_r1, bgp_asn=12, ip_address=self.cgw_ip, typ='ipsec.1')
        wait_customer_gateways_state(self.conns[0], [ret.response.customerGateway.customerGatewayId], state='available')
        assert ret.status_code == 200
        assert ret.response.customerGateway.bgpAsn == '12'
        assert ret.response.customerGateway.ipAddress == self.cgw_ip
        assert ret.response.customerGateway.state == 'available'

    def test_T763_invalid_bgp_asn(self):
        try:
            create_customer_gateway(self.a1_r1, bgp_asn=-1, ip_address=self.cgw_ip, typ='ipsec.1')
            assert False, 'Call should not have been successful, invalid bgp asn'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Value (-1) for parameter bgpAsn is in invalid range. Invalid Format.')
        try:
            create_customer_gateway(self.a1_r1, bgp_asn=4294967296, ip_address=self.cgw_ip, typ='ipsec.1')
            assert False, 'Call should not have been successful, invalid bgp asn'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Value (4294967296) for parameter bgpAsn is in invalid range. Invalid Format.')
        try:
            create_customer_gateway(self.a1_r1, bgp_asn='toto', ip_address=self.cgw_ip, typ='ipsec.1')
            assert False, 'Call should not have been successful, invalid bgp asn'
        except OscApiException as error:
            if error.status_code == 400 and error.error_code == 'OWS.Error' and error.message == 'Request is not valid.':
                known_error('TINA-4239', 'Incorrect error message')
            assert False, 'Remove known error code'
            assert_error(error, 400, 'xxx', '')

    def test_T764_invalid_param(self):
        try:
            create_customer_gateway(self.a1_r1, toto='toto', bgp_asn=12, ip_address=self.cgw_ip, typ='ipsec.1')
            known_error('TINA-4239', 'Missing error message')
            assert False, 'Call should not have been successful, invalid extra parameter'
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert_error(error, 400, 'xxx', '')

    def test_T4504_with_reserved_ip(self):
        try:
            create_customer_gateway(self.a1_r1, bgp_asn=12, ip_address='192.168.1.3', typ='ipsec.1')
            known_error('TINA-5642', 'Create customer gateway with reserved ip_address should not have been successful')
            assert False, 'Call should not have been successful, invalid extra parameter'
        except OscApiException as error:
            assert False, 'Remove known error'
            assert_error(error, 400, 'InvalidParameterValue', 'Value for parameter ipAddress is a private address: 192.168.1.3')

    def test_T4925_with_private_ip(self):
        create_customer_gateway(self.a1_r1, bgp_asn=12, ip_address='169.1.1.1', typ='ipsec.1')
