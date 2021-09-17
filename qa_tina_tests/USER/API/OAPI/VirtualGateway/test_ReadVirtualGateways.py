import pytest

from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest

NUM_VGW = 4


class Test_ReadVirtualGateways(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.vgw_ids = []
        super(Test_ReadVirtualGateways, cls).setup_class()
        try:
            for _ in range(NUM_VGW):
                cls.vgw_ids.append(cls.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId)
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            for vgw_id in cls.vgw_ids:
                cls.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id)
        finally:
            super(Test_ReadVirtualGateways, cls).teardown_class()

    def test_T2373_valid_params(self):
        self.a1_r1.oapi.ReadVirtualGateways()

    def test_T2374_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadVirtualGateways(DryRun=True)
        misc.assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3445_other_account(self):
        ret = self.a2_r1.oapi.ReadVirtualGateways().response.VirtualGateways
        assert not ret

    @pytest.mark.tag_sec_confidentiality
    def test_T3446_other_account_with_filter(self):
        ret = self.a2_r1.oapi.ReadVirtualGateways(Filters={'VirtualGatewayIds': self.vgw_ids}).response.VirtualGateways
        assert not ret

    def test_T3653_filters_connection_types_ipsec1(self):
        ret = self.a1_r1.oapi.ReadVirtualGateways(Filters={'ConnectionTypes': ['ipsec.1']}).response.VirtualGateways
        assert len(ret) == NUM_VGW

    def test_T3654_filters_connection_types_invalid(self):
        ret = self.a1_r1.oapi.ReadVirtualGateways(Filters={'ConnectionTypes': ['invalid']}).response.VirtualGateways
        assert len(ret) == 0

    def test_T3655_filters_link_net_ids(self):
        ret = self.a1_r1.oapi.ReadVirtualGateways(Filters={'LinkNetIds': ['net-12345678']}).response.VirtualGateways
        assert len(ret) == 0

    def test_T3656_filters_link_states(self):
        ret = self.a1_r1.oapi.ReadVirtualGateways(Filters={'LinkStates': ['attached']}).response.VirtualGateways
        assert len(ret) == 0

    def test_T3657_filters_states(self):
        ret = self.a1_r1.oapi.ReadVirtualGateways(Filters={'States': ['available']}).response.VirtualGateways
        assert len(ret) == NUM_VGW

    def test_T3658_filters_virtual_gateway_ids(self):
        ret = self.a1_r1.oapi.ReadVirtualGateways(Filters={'VirtualGatewayIds': [self.vgw_ids[0]]}).response.VirtualGateways
        assert len(ret) == 1

    def test_T5981_with_tag_filter(self):
        indexes, _ = misc.execute_tag_tests(self.a1_r1, 'VirtualGateway', self.vgw_ids, 'oapi.ReadVirtualGateways', 'VirtualGateways.VirtualGatewayId')
        assert indexes == [3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 19, 20, 24, 25, 26, 27, 28, 29]
        known_error('API-399', 'Read calls do not support wildcards in tag filtering')
