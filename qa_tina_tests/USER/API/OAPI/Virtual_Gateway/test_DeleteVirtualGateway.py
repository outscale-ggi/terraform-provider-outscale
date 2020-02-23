from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.misc import assert_dry_run, assert_oapi_error
from qa_tina_tools.tools.tina.wait_tools import wait_vpn_gateways_state
import pytest
from osc_common.exceptions.osc_exceptions import OscApiException


class Test_DeleteVirtualGateway(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteVirtualGateway, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteVirtualGateway, cls).teardown_class()

    def test_T2369_valid_params(self):
        vgw_id = None
        try:
            vgw_id = self.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
            wait_vpn_gateways_state(self.a1_r1, [vgw_id], state='available')
            self.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id)
            vgw_id = None
        finally:
            if vgw_id:
                try:
                    self.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id)
                except:
                    pass

    def test_T2370_valid_params_dry_run(self):
        vgw_id = None
        try:
            vgw_id = self.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
            wait_vpn_gateways_state(self.a1_r1, [vgw_id], state='available')
            ret = self.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id, DryRun=True)
            assert_dry_run(ret)
        finally:
            if vgw_id:
                try:
                    self.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id)
                except:
                    pass

    @pytest.mark.tag_sec_confidentiality
    def test_T3538_with_other_user(self):
        vgw_id = None
        try:
            vgw_id = self.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
            wait_vpn_gateways_state(self.a1_r1, [vgw_id], state='available')
            self.a2_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5068')
        finally:
            if vgw_id:
                try:
                    self.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id)
                except:
                    pass

    def test_T3539_without_params(self):
        vgw_id = None
        try:
            vgw_id = self.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
            wait_vpn_gateways_state(self.a1_r1, [vgw_id], state='available')
            self.a2_r1.oapi.DeleteVirtualGateway()
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        finally:
            if vgw_id:
                try:
                    self.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id)
                except:
                    pass
