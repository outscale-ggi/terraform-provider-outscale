
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import oapi, wait
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import known_error
from qa_test_tools.misc import assert_oapi_error, id_generator
from qa_test_tools.config.configuration import Configuration


class Test_UpdateVpnConnection(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.net_info = None
        cls.cg_id = None
        cls.vpn_id = None
        cls.vgw_id = None
        cls.cgw_ip = None
        super(Test_UpdateVpnConnection, cls).setup_class()
        try:
            cls.net_info = oapi.create_Net(cls.a1_r1)
            cls.cgw_ip = Configuration.get('ipaddress', 'cgw_ip')
            cls.vgw_id = cls.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
            cls.cg_id = cls.a1_r1.oapi.CreateClientGateway(BgpAsn=65000, PublicIp=cls.cgw_ip,
                                                           ConnectionType='ipsec.1').response.ClientGateway.ClientGatewayId
            ret = cls.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=cls.cg_id,
                                                      VirtualGatewayId=cls.vgw_id,
                                                      ConnectionType='ipsec.1',
                                                      StaticRoutesOnly=True)
            cls.vpn_id = ret.response.VpnConnection.VpnConnectionId
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpn_id:
                cls.a1_r1.oapi.DeleteVpnConnection(VpnConnectionId=cls.vpn_id)
                wait.wait_VpnConnections_state(cls.a1_r1, [cls.vpn_id], 'deleted')
            if cls.cg_id:
                cls.a1_r1.oapi.DeleteClientGateway(ClientGatewayId=cls.cg_id)
            if cls.vgw_id:
                cls.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=cls.vgw_id)
                wait.wait_VpnConnections_state(cls.a1_r1, [cls.vpn_id], 'deleted')
            if cls.net_info:
                oapi.delete_Net(cls.a1_r1, cls.net_info)
        finally:
            super(Test_UpdateVpnConnection, cls).teardown_class()

    def test_T5934_valid_case(self):
        try:
            self.a1_r1.oapi.UpdateVpnConnection(VpnConnectionId=self.vpn_id,
                                            VpnOptions={"TunnelInsideIpRange":"169.254.254.8/30"})
        except OscApiException as error:
            if error.status_code == 500 and error.message == 'InternalError':
                known_error("TINA-6683", "oapi.UpdateVpnConnection InternalError")
            assert False, "remove known error code"
            assert_oapi_error(error, 400, 'xx', 'xx')

    def test_T5935_required_params_only(self):
        try:
            self.a1_r1.oapi.UpdateVpnConnection(VpnConnectionId=self.vpn_id)
        except OscApiException as error:
            if error.status_code == 500 and error.message == 'InternalError':
                known_error("TINA-6683", "oapi.UpdateVpnConnection InternalError")
            assert False, "remove known error code"
            assert_oapi_error(error, 400, 'xx', 'xx')

    def test_T5936_non_existant_vpn_id(self):
        try:
            self.a1_r1.oapi.UpdateVpnConnection(VpnConnectionId="vpn-12345678")
        except OscApiException as error:
            if error.status_code == 400 and error.message == 'DefaultError':
                known_error("TINA-6683", "oapi.UpdateVpnConnection DefaultError")
            assert False, "remove known error code"
            assert_oapi_error(error, 400, 'xx', 'xx')

    def test_T5937_malformed_vpn_id(self):
        try:
            self.a1_r1.oapi.UpdateVpnConnection(VpnConnectionId="xxx-12345678")
        except OscApiException as error:
            if error.status_code == 400 and error.message == 'DefaultError':
                known_error("TINA-6683", "oapi.UpdateVpnConnection DefaultError")
            assert False, "remove known error code"
            assert_oapi_error(error, 400, 'xx', 'xx')
    def test_T5938_with_invalid_PreSharedKey(self):
        try:
            self.a1_r1.oapi.UpdateVpnConnection(VpnConnectionId=self.vpn_id, VpnOptions={"Phase2Options":{"PreSharedKey":"1234567890SDFGHJK"}})
        except OscApiException as error:
            if error.status_code == 500 and error.message == 'InternalError':
                known_error("TINA-6683", "oapi.UpdateVpnConnection InternalError")
            assert False, "remove known error code"
            assert_oapi_error(error, 400, 'xx', 'xx')

    def test_T5939_with_valid_PreSharedKey(self):
        presharedkey = id_generator(size=26)
        try:
            self.a1_r1.oapi.UpdateVpnConnection(VpnConnectionId=self.vpn_id, VpnOptions={"Phase2Options":{"PreSharedKey":presharedkey}})
        # TODO add check response
        except OscApiException as error:
            if error.status_code == 500 and error.message == 'InternalError':
                known_error("TINA-6683", "oapi.UpdateVpnConnection InternalError")
            assert False, "remove known error code"
    def test_T5940_with_all_parameters(self):
        try:
            self.a1_r1.oapi.UpdateVpnConnection(VpnConnectionId=self.vpn_id,
                                   VpnOptions={"Phase1Options":{"DpdTimeoutAction":"test", "DpdTimeoutSeconds":1,"Phase1DhGroupNumbers":[1],
                                                                "Phase1EncryptionAlgorithms":["test"], "Phase1IntegrityAlgorithms":["test"],
                                                                "Phase1LifetimeSeconds":1, "ReplayWindowSize":1, "StartupAction":"xx"},
                                                "Phase2Options":{"Phase2DhGroupNumbers": [0], "Phase2EncryptionAlgorithms":
                                                                 ["test"], "Phase2IntegrityAlgorithms": ["test"],
                                                                 "Phase2LifetimeSeconds": 0, "PreSharedKey":"PreSharedKey"}})
            assert False, 'correct test after fix TINA-6683 by adding check response'
        except OscApiException as error:
            if error.status_code == 500 and error.message == 'InternalError':
                known_error("TINA-6683", "oapi.UpdateVpnConnection InternalError")
            assert False, "remove known error code"
# TODO add functionnal test
