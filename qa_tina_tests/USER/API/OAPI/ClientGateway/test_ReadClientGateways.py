
import pytest

from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tests.USER.API.OAPI.ClientGateway.ClientGateway import validate_client_gateway

NUM_CGW = 4

class Test_ReadClientGateways(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.cg_ids = []
        super(Test_ReadClientGateways, cls).setup_class()
        for i in range(NUM_CGW - 1):
            cls.cg_ids.append(cls.a1_r1.oapi.CreateClientGateway(
                BgpAsn=65002, PublicIp='172.10.8.{}'.format(i), ConnectionType='ipsec.1').response.ClientGateway.ClientGatewayId)
        cls.cg_ids.append(cls.a1_r1.oapi.CreateClientGateway(
            BgpAsn=2578, PublicIp='192.10.8.9', ConnectionType='ipsec.1').response.ClientGateway.ClientGatewayId)

    @classmethod
    def teardown_class(cls):
        try:
            for cg_id in cls.cg_ids:
                cls.a1_r1.oapi.DeleteClientGateway(ClientGatewayId=cg_id)
        finally:
            super(Test_ReadClientGateways, cls).teardown_class()

    def test_T3319_empty_filters(self):
        ret = self.a1_r1.oapi.ReadClientGateways().response.ClientGateways
        assert len(ret) >= 2
        for cgtw in ret:
            validate_client_gateway(cgtw)

    def test_T3320_filters_client_gateway_ids_id1(self):
        ret = self.a1_r1.oapi.ReadClientGateways(Filters={'ClientGatewayIds': [self.cg_ids[0]]}).response.ClientGateways
        for cgtw in ret:
            validate_client_gateway(cgtw, expected_cg={
                'PublicIp': '172.10.8.0',
                'BgpAsn': 65002,
                'ConnectionType': 'ipsec.1',
                'ClientGatewayId': self.cg_ids[0]
            })

    def test_T3321_filters_client_gateway_ids_id2(self):
        ret = self.a1_r1.oapi.ReadClientGateways(Filters={'ClientGatewayIds': [self.cg_ids[NUM_CGW - 1]]}).response.ClientGateways
        for cgtw in ret:
            validate_client_gateway(cgtw, expected_cg={
                'PublicIp': '192.10.8.9',
                'BgpAsn': 2578,
                'ConnectionType': 'ipsec.1',
                'ClientGatewayId': self.cg_ids[NUM_CGW - 1]
            })

    def test_T3322_filters_bgp_asn(self):
        ret = self.a1_r1.oapi.ReadClientGateways(Filters={'BgpAsns': [65002]}).response.ClientGateways
        for cgtw in ret:
            validate_client_gateway(cgtw, expected_cg={
                'BgpAsn': 65002,
            })

    def test_T3323_filters_connection_types(self):
        ret = self.a1_r1.oapi.ReadClientGateways(Filters={'ConnectionTypes': ['ipsec.1']}).response.ClientGateways
        for cgtw in ret:
            validate_client_gateway(cgtw, expected_cg={
                'ConnectionType': 'ipsec.1',
            })

    def test_T3324_filters_public_ips(self):
        ret = self.a1_r1.oapi.ReadClientGateways(Filters={'PublicIps': ['172.10.8.9']}).response.ClientGateways
        for cgtw in ret:
            validate_client_gateway(cgtw, expected_cg={
                'PublicIp': '172.10.8.9',
            })

    def test_T3325_filters_unknown_public_ips(self):
        ret = self.a1_r1.oapi.ReadClientGateways(Filters={'PublicIps': ['12.10.8.9']}).response.ClientGateways
        assert len(ret) == 0

    def test_T3326_filters_state_available(self):
        ret = self.a1_r1.oapi.ReadClientGateways(Filters={'States': ['available']}).response.ClientGateways
        for cgtw in ret:
            validate_client_gateway(cgtw, expected_cg={'State': 'available'})

    def test_T3327_filters_state_deleted(self):
        ret = self.a1_r1.oapi.ReadClientGateways(Filters={'States': ['deleted']}).response.ClientGateways
        for cgtw in ret:
            validate_client_gateway(cgtw, expected_cg={'State': 'deleted'})

    def test_T3697_dry_run(self):
        ret = self.a1_r1.oapi.ReadClientGateways(DryRun=True)
        misc.assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3698_with_other_user(self):
        ret = self.a2_r1.oapi.ReadClientGateways().response.ClientGateways
        assert len(ret) == 0

    def test_T5967_with_tag_filter(self):
        indexes, _ = misc.execute_tag_tests(self.a1_r1, 'ClientGateway', self.cg_ids,
                                            'oapi.ReadClientGateways', 'ClientGateways.ClientGatewayId')
        assert indexes == [3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 19, 20, 24, 25, 26, 27, 28, 29]
        known_error('API-399', 'Read calls do not support wildcards in tag filtering')
