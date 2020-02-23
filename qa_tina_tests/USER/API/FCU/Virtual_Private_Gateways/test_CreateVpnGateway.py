from osc_common.exceptions import OscApiException
from qa_common_tools.misc import assert_error
from qa_common_tools.test_base import OscTestSuite


class Test_CreateVpnGateway(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateVpnGateway, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateVpnGateway, cls).teardown_class()

    def test_T4377_without_params(self):
        try:
            self.a1_r1.fcu.CreateVpnGateway()
            assert False, "call should not have been successful, bad parameter"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Client.InvalidParameterValue: Value (None) '
                                                              'for parameter type is invalid. Invalid gateway type.')

    def test_T4378_with_valid_type(self):
        ret = self.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1')
        assert ret.response.requestId
        assert ret.response.vpnGateway
        assert ret.response.vpnGateway.type == 'ipsec.1'
        self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=ret.response.vpnGateway.vpnGatewayId)

    def test_T4379_with_invalid_type(self):
        try:
            self.a1_r1.fcu.CreateVpnGateway(Type='ipsec.3')
            assert False, "call should not have been successful, bad parameter"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Client.InvalidParameterValue: Value (ipsec.3) '
                                                              'for parameter type is invalid. Invalid gateway type.')
