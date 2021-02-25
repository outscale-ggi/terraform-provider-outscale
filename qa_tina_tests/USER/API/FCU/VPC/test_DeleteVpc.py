from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.wait import wait_VpnConnections_state
from qa_tina_tools.tools.tina.wait_tools import wait_vpn_gateways_attachment_state, wait_customer_gateways_state


class Test_DeleteVpc(OscTestSuite):

    def test_T613_without_param(self):
        try:
            self.a1_r1.fcu.DeleteVpc()
            assert False, "call should not have been successful, missing param"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "Parameter cannot be empty: VpcID"

    def test_T1303_without_param_existing_vpc(self):
        vpc_id = None
        try:
            ret = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            vpc_id = ret.response.vpc.vpcId
            self.a1_r1.fcu.DeleteVpc(VpcId='vpc-12345678')
            assert False, "call should not have been successful, invalid vpc-id"
        except OscApiException as err:
            assert_error(err, 400, 'InvalidVpcID.NotFound', "The vpc ID 'vpc-12345678' does not exist")
        finally:
            if vpc_id:
                self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)

    def test_T273_with_valid_vpc_id(self):
        ret = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
        vpc_id = ret.response.vpc.vpcId
        self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)

    def test_T614_with_invalid_vpc_id(self):
        try:
            self.a1_r1.fcu.DeleteVpc(VpcId='toto')
            assert False, "call should not have been successful, invalid vpc-id"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "Invalid ID received: toto. Expected format: vpc-"

    def test_T733_delete_from_another_account(self):
        try:
            ret = self.a2_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            vpc_id = ret.response.vpc.vpcId
            self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
            assert False, "call should not have been successful, invalid vpc-id"
        except OscApiException as err:
            try:
                self.a2_r1.fcu.DeleteVpc(VpcId=vpc_id)
            except Exception:
                self.logger.info("Could not delete vpc -> " + vpc_id)
            assert err.status_code == 400
            assert err.message == "The vpc ID '%s' does not exist" % vpc_id

    def test_T5543_with_attached_vpn_connection(self):
        vpc_id = None
        cgw_id = None
        vgw_id = None
        attach = None
        vpn_conn = None
        try:
            vpc_id = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16')).response.vpc.vpcId
            cgw_id = self.a1_r1.fcu.CreateCustomerGateway(BgpAsn=12, IpAddress=Configuration.get('ipaddress', 'cgw_ip'),
                                                      Type='ipsec.1').response.customerGateway.customerGatewayId
            vgw_id = self.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1').response.vpnGateway.vpnGatewayId
            attach = self.a1_r1.fcu.AttachVpnGateway(VpcId=vpc_id, VpnGatewayId=vgw_id)
            vpn_conn = self.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=cgw_id, Type='ipsec.1', VpnGatewayId=vgw_id)
            self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
            assert False, "call should not have been successful, invalid vpc-id"
        except OscApiException as err:
            assert_error(err, 400, 'DependencyViolation', "Resource has a dependent object")
        finally:
            if vpn_conn:
                self.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn_conn.response.vpnConnection.vpnConnectionId)
                wait_VpnConnections_state(self.a1_r1, [vpn_conn.response.vpnConnection.vpnConnectionId], 'deleted')
            if attach:
                self.a1_r1.fcu.DetachVpnGateway(VpcId=vpc_id, VpnGatewayId=vgw_id)
                wait_vpn_gateways_attachment_state(self.a1_r1, [vgw_id], 'detached')
                self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=vgw_id)
            if cgw_id:
                self.a1_r1.fcu.DeleteCustomerGateway(CustomerGatewayId=cgw_id)
                wait_customer_gateways_state(self.a1_r1, [cgw_id], state='deleted')
            if vpc_id:
                self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
