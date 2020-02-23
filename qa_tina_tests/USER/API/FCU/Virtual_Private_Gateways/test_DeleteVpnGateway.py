from osc_common.exceptions import OscApiException
from qa_common_tools.misc import assert_error, id_generator
from qa_common_tools.test_base import OscTestSuite, known_error


class Test_DeleteVpnGateway(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteVpnGateway, cls).setup_class()
        cls.vpn_gateway_id = None

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteVpnGateway, cls).teardown_class()

    def setup_method(self, method):
        super(Test_DeleteVpnGateway, self).setup_method(method)
        try:
            self.vpn_gateway_id = self.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1').response.vpnGateway.vpnGatewayId
        except Exception:
            try:
                self.teardown_class()
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.vpn_gateway_id:
                self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=self.vpn_gateway_id)
        finally:
            super(Test_DeleteVpnGateway, self).teardown_method(method)

    def test_T4380_without_params(self):
        try:
            self.a1_r1.fcu.DeleteVpnGateway()
            known_error('TINA-5233', 'call should not have been successful, None parameter')
            assert False, "call should not have been successful, bad parameter"
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert_error(error, 400, 'InvalidVpnGatewayID.NotFound', "The VpnGatewayId 'None' does not exist")

    def test_T4381_with_invalid_id(self):
        try:
            vp_id = id_generator(prefix='vgw-', size=8)
            self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=vp_id)
            assert False, "call should not have been successful, bad parameter"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpnGatewayID.NotFound', "The VpnGatewayId '{}' does not exist".
                         format(str(vp_id)))

    def test_T4382_with_valid_id(self):
        ret = self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=self.vpn_gateway_id)
        assert ret.response.osc_return

    def test_T4384_with_id_from_other_account(self):
        try:
            self.a2_r1.fcu.DeleteVpnGateway(VpnGatewayId=self.vpn_gateway_id)
            assert False, "call should not have been successful, bad parameter"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpnGatewayID.NotFound', "The VpnGatewayId '{}' does not exist".
                         format(self.vpn_gateway_id))
