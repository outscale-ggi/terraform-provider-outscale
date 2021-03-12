import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import wait
from qa_tina_tools.tools.tina import wait_tools
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_customer_gateways
from qa_tina_tools.tools.tina.create_tools import create_customer_gateway


class Test_DeleteCustomerGateway(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.gateway_id_list = None
        cls.cgw_ip = Configuration.get('ipaddress', 'cgw_ip')
        super(Test_DeleteCustomerGateway, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteCustomerGateway, cls).teardown_class()

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        try:
            self.gateway_id_list = []
            for i in range(2):
                ret = create_customer_gateway(self.conns[i], bgp_asn=12, ip_address=self.cgw_ip, typ='ipsec.1')
                wait_tools.wait_customer_gateways_state(self.conns[i], [ret.response.customerGateway.customerGatewayId], state='available')
                assert ret.response.customerGateway.bgpAsn == '12'
                assert ret.response.customerGateway.ipAddress == self.cgw_ip
                assert ret.response.customerGateway.state == 'available'
                self.gateway_id_list.append({'id': ret.response.customerGateway.customerGatewayId})
        except AssertionError as error:
            try:
                self.teardown_method(method)
            finally:
                raise error

    def teardown_method(self, method):
        try:
            cleanup_customer_gateways(self.conns[0])
            cleanup_customer_gateways(self.conns[1])
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T770_without_argv(self):
        try:
            self.conns[0].fcu.DeleteCustomerGateway()
            pytest.fail('Call should not have been successful, no arguments')
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Parameter cannot be empty: CustomerGatewayID")

    def test_T771_invalid_cgw_id(self):
        try:
            self.conns[0].fcu.DeleteCustomerGateway(CustomerGatewayId="toto")
            pytest.fail('Call should not have been successful, invalid gateway id')
        except OscApiException as error:
            assert_error(error, 400, "InvalidCustomerGatewayID.Malformed", "Invalid ID received: toto. Expected format: cgw-")
        try:
            self.conns[0].fcu.DeleteCustomerGateway(CustomerGatewayId="cgw-xxxxxxxx")
            pytest.fail('Call should not have been successful, invalid gateway id')
        except OscApiException as error:
            assert_error(error, 400, "InvalidCustomerGatewayID.Malformed", "Invalid ID received: cgw-xxxxxxxx")
        try:
            self.conns[0].fcu.DeleteCustomerGateway(CustomerGatewayId=self.gateway_id_list[0]['id'].replace('cgw-', 'cgw-xxx'))
            pytest.fail('Call should not have been successful, invalid gateway id')
        except OscApiException as error:
            assert_error(error, 400, "InvalidCustomerGatewayID.Malformed",
                         "Invalid ID received: {}".format(self.gateway_id_list[0]['id'].replace('cgw-', 'cgw-xxx')))

    def test_T772_valid_cgw_id(self):
        self.conns[0].fcu.DeleteCustomerGateway(CustomerGatewayId=self.gateway_id_list[0]['id'])
        wait_tools.wait_customer_gateways_state(self.conns[0], [self.gateway_id_list[0]['id']], state='deleted')

    def test_T773_another_account_cgw_id(self):
        try:
            self.conns[0].fcu.DeleteCustomerGateway(CustomerGatewayId=self.gateway_id_list[1]['id'])
            pytest.fail('Call should not have been successful, id from another account')
        except OscApiException as error:
            assert_error(error, 400, "InvalidCustomerGatewayID.NotFound",
                         "The customerGateway ID '{}' does not exist".format(self.gateway_id_list[1]['id']))

    def test_T774_deleted_cgw_id(self):
        self.conns[0].fcu.DeleteCustomerGateway(CustomerGatewayId=self.gateway_id_list[0]['id'])
        wait_tools.wait_customer_gateways_state(self.conns[0], [self.gateway_id_list[0]['id']], state='deleted')
        self.conns[0].fcu.DeleteCustomerGateway(CustomerGatewayId=self.gateway_id_list[0]['id'])

    def test_T1388_with_existing_vpn_connection(self):
        vpn_id = None
        vgw_id = None
        # TODO fill test , customer gateway cannot be deleted before vpn connection
        try:
            ret = self.a1_r1.fcu.CreateVpnGateway(Type="ipsec.1")
            vgw_id = ret.response.vpnGateway.vpnGatewayId
            ret = self.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=self.gateway_id_list[0]['id'], Type='ipsec.1', VpnGatewayId=vgw_id)
            vpn_id = ret.response.vpnConnection.vpnConnectionId
            try:
                self.a1_r1.fcu.DeleteCustomerGateway(CustomerGatewayId=self.gateway_id_list[0]['id'])
            except OscApiException as error:
                assert_error(error, 400, 'IncorrectState', 'The customer gateway is in use.')
        finally:
            if vpn_id:
                self.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn_id)
                wait.wait_VpnConnections_state(self.a1_r1, vpn_connection_ids=[vpn_id], state="deleted", wait_time=5, threshold=40, cleanup=True)
            if vgw_id:
                self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=vgw_id)
