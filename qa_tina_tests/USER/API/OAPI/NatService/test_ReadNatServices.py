# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import pytest

from qa_test_tools.misc import assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_nat
from qa_tina_tools.tools.tina.delete_tools import delete_nat
from qa_tina_tools.tools.tina.info_keys import NAT_GW, VPC_INFO, VPC_ID, SUBNETS, \
    SUBNET_ID


class Test_ReadNatServices(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadNatServices, cls).setup_class()
        cls.nat_infos = []
        try:
            for _ in range(2):
                cls.nat_infos.append(create_nat(cls.a1_r1))
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.nat_infos[0][NAT_GW].id], Tags=[{'Key': 'key', 'Value': 'value'}])
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            for nat_info in cls.nat_infos:
                delete_nat(cls.a1_r1, nat_info)
        finally:
            super(Test_ReadNatServices, cls).teardown_class()

    def test_T2541_dry_run(self):
        ret = self.a1_r1.oapi.ReadNatServices(DryRun=True)
        assert_dry_run(ret)

    def test_T2542_without_param(self):
        ret = self.a1_r1.oapi.ReadNatServices()
        assert len(ret.response.NatServices) == 2

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
        ret = self.a2_r1.oapi.ReadNatServices(Filters={'NatServiceIds': [self.nat_infos[0][NAT_GW].id]}).response.NatServices
        assert not ret

    def test_T3829_with_nat_service_ids_filter(self):
        ret = self.a1_r1.oapi.ReadNatServices(Filters={'NatServiceIds': [self.nat_infos[0][NAT_GW].id]}).response.NatServices
        assert len(ret) == 1
        assert len(ret[0].Tags) == 1

    def test_T3830_with_net_ids_filter(self):
        ret = self.a1_r1.oapi.ReadNatServices(Filters={'NetIds': [self.nat_infos[0][VPC_INFO][VPC_ID]]}).response.NatServices
        assert len(ret) == 1

    def test_T3831_with_states_filter(self):
        ret = self.a1_r1.oapi.ReadNatServices(Filters={'States': ['available']}).response.NatServices
        assert len(ret) == 2

    def test_T3832_with_subnet_ids_filter(self):
        ret = self.a1_r1.oapi.ReadNatServices(Filters={'SubnetIds': [self.nat_infos[0][VPC_INFO][SUBNETS][0][SUBNET_ID]]}).response.NatServices
        assert len(ret) == 1
