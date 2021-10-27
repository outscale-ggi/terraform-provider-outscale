import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from specs import check_oapi_error
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_dry_run
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.wait_tools import wait_vpn_gateways_state, \
    wait_vpcs_state


class Test_UnlinkVirtualGateway(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.net_id = None
        cls.vgw_id = None
        cls.ret_link = None
        super(Test_UnlinkVirtualGateway, cls).setup_class()
        try:
            cls.net_id = cls.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            wait_vpcs_state(cls.a1_r1, [cls.net_id], state='available')
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.net_id:
                cls.a1_r1.oapi.DeleteNet(NetId=cls.net_id)
        finally:
            super(Test_UnlinkVirtualGateway, cls).teardown_class()

    def setup_method(self, method):
        self.vgw_id = None
        self.ret_link = None
        OscTinaTest.setup_method(self, method)
        try:
            self.vgw_id = self.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
            wait_vpn_gateways_state(self.a1_r1, [self.vgw_id], state='available')
            self.ret_link = self.a1_r1.oapi.LinkVirtualGateway(VirtualGatewayId=self.vgw_id, NetId=self.net_id)
            wait_vpn_gateways_state(self.a1_r1, [self.vgw_id], state='available')
        except:
            try:
                self.teardown_method(method)
            finally:
                raise

    def teardown_method(self, method):
        try:
            if self.ret_link:
                try:
                    self.a1_r1.oapi.UnlinkVirtualGateway(VirtualGatewayId=self.vgw_id, NetId=self.net_id)
                    wait_vpn_gateways_state(self.a1_r1, [self.vgw_id], state='available')
                except:
                    print('Could not unlink virtual gateway')
            if self.vgw_id:
                try:
                    self.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=self.vgw_id)
                except:
                    print('Could not delete virtual gateway')
        finally:
            OscTinaTest.teardown_method(self, method)

    def test_T2375_valid_params(self):
        self.a1_r1.oapi.UnlinkVirtualGateway(VirtualGatewayId=self.vgw_id, NetId=self.net_id)
        self.ret_link = None
        wait_vpn_gateways_state(self.a1_r1, [self.vgw_id], state='available')

    def test_T2376_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.UnlinkVirtualGateway(VirtualGatewayId=self.vgw_id, NetId=self.net_id, DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3530_other_account(self):
        try:
            self.a2_r1.oapi.UnlinkVirtualGateway(VirtualGatewayId=self.vgw_id, NetId=self.net_id)
            self.ret_link = None
            wait_vpn_gateways_state(self.a1_r1, [self.vgw_id], state='available')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5068, id=self.vgw_id)
