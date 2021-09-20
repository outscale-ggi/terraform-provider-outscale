
import pytest

from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina import create_tools, delete_tools
from qa_tina_tools.tools.tina import info_keys

NUM_NAT_SERVICES = 4

class Test_ReadNatServices(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.nat_ids = []
        cls.nat_infos = []
        super(Test_ReadNatServices, cls).setup_class()
        try:
            for _ in range(NUM_NAT_SERVICES):
                nat_info = create_tools.create_nat(cls.a1_r1)
                cls.nat_infos.append(nat_info)
                cls.nat_ids.append(nat_info[info_keys.NAT_GW].id)
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            for nat_info in cls.nat_infos:
                delete_tools.delete_nat(cls.a1_r1, nat_info)
        finally:
            super(Test_ReadNatServices, cls).teardown_class()

    def test_T2541_dry_run(self):
        ret = self.a1_r1.oapi.ReadNatServices(DryRun=True)
        misc.assert_dry_run(ret)

    def test_T2542_without_param(self):
        ret = self.a1_r1.oapi.ReadNatServices()
        assert len(ret.response.NatServices) == NUM_NAT_SERVICES

    # TODO: add tests:
    # - invalid dry run
    # - valid filter
    # - invalid filter

    # def test_without_filters(self):
    #    assert(len(self.a1_r1.oapi.ReadNatServices(
    #        Filters={}).response.NatServices) >= 2)

    # def test_with_state_filter(self):
    #    assert(len(self.a1_r1.oapi.ReadNatServices(
    #        Filters={'States': ['available']}).response.NatServices) == 2)

    # def test_with_nat_id_filter(self):
    #    assert(len(self.a1_r1.oapi.ReadNatServices(
    #        Filters={'NatServiceIds': [self.nat_service_id_1]}).response.NatServices) == 1)

    # def test_with_subnet_id_filter(self):
    #    assert(len(self.a1_r1.oapi.ReadNatServices(
    #        Filters={'SubnetIds': [self.subnet_id_1, self.subnet_id_2],
    #                 'States': ['available']}).response.NatServices) == 2)

    # def test_with_net_id_filter(self):
    #    assert(len(self.a1_r1.oapi.ReadNatServices(
    #        Filters={'NetIds': [self.net_id_2], 'States': ['available']}).response.NatServices) == 1)

    @pytest.mark.tag_sec_confidentiality
    def test_T3436_other_account(self):
        ret = self.a2_r1.oapi.ReadNatServices().response.NatServices
        assert not ret

    @pytest.mark.tag_sec_confidentiality
    def test_T3437_other_account_with_filter(self):
        ret = self.a2_r1.oapi.ReadNatServices(Filters={'NatServiceIds': [self.nat_infos[0][info_keys.NAT_GW].id]}).response.NatServices
        assert not ret

    def test_T3829_with_nat_service_ids_filter(self):
        ret = self.a1_r1.oapi.ReadNatServices(Filters={'NatServiceIds': [self.nat_infos[0][info_keys.NAT_GW].id]}).response.NatServices
        assert len(ret) == 1

    def test_T3830_with_net_ids_filter(self):
        ret = self.a1_r1.oapi.ReadNatServices(Filters={'NetIds': [self.nat_infos[0][info_keys.VPC_INFO][info_keys.VPC_ID]]}).response.NatServices
        assert len(ret) == 1

    def test_T3831_with_states_filter(self):
        ret = self.a1_r1.oapi.ReadNatServices(Filters={'States': ['available']}).response.NatServices
        assert len(ret) == NUM_NAT_SERVICES

    def test_T3832_with_subnet_ids_filter(self):
        ret = self.a1_r1.oapi.ReadNatServices(
            Filters={'SubnetIds': [self.nat_infos[0][info_keys.VPC_INFO][info_keys.SUBNETS][0][info_keys.SUBNET_ID]]}).response.NatServices
        assert len(ret) == 1

    def test_T5970_with_tag_filter(self):
        indexes, _ = misc.execute_tag_tests(self.a1_r1, 'NatService', self.nat_ids,
                               'oapi.ReadNatServices', 'NatServices.NatServiceId')
        assert indexes == [3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 19, 20, 24, 25, 26, 27, 28, 29]
        known_error('API-399', 'Read calls do not support wildcards in tag filtering')
