

import re

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_public_ip
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, delete_public_ip
from qa_tina_tools.tools.tina.info_keys import VPC_ID, SUBNETS, SUBNET_ID, PUBLIC_IP
from qa_tina_tools.tools.tina.wait_tools import wait_nat_gateways_state


class Test_CreateNatService(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateNatService, cls).setup_class()
        cls.vpc_info = None
        cls.pub_ip_info = None
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, default_rtb=True, no_ping=True)
            cls.pub_ip_info = create_public_ip(cls.a1_r1, domain='vpc')
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.pub_ip_info:
                delete_public_ip(cls.a1_r1, cls.pub_ip_info)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_CreateNatService, cls).teardown_class()

    def test_T2527_dry_run(self):
        ret = self.a1_r1.oapi.CreateNatService(PublicIpId=self.pub_ip_info[PUBLIC_IP].id, SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID], DryRun=True)
        assert_dry_run(ret)

    def test_T2528_with_valid_param(self):
        nat_id = None
        try:
            ret = self.a1_r1.oapi.CreateNatService(PublicIpId=self.pub_ip_info[PUBLIC_IP].id, SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            nat_id = ret.response.NatService.NatServiceId
            assert re.search(r"(nat-[a-zA-Z0-9]{8})", ret.response.NatService.NatServiceId)
            assert ret.response.NatService.NetId == self.vpc_info[VPC_ID]
            assert ret.response.NatService.PublicIps[0].PublicIpId
            assert ret.response.NatService.PublicIps[0].PublicIp == self.pub_ip_info[PUBLIC_IP].ip
            assert ret.response.NatService.State == 'available'
            assert ret.response.NatService.SubnetId == self.vpc_info[SUBNETS][0][SUBNET_ID]
        finally:
            if nat_id:
                self.a1_r1.oapi.DeleteNatService(NatServiceId=nat_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[nat_id], state='deleted')

    def test_T2529_without_link_id(self):
        try:
            self.a1_r1.oapi.CreateNatService(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2530_without_subnet_id(self):
        try:
            self.a1_r1.oapi.CreateNatService(PublicIpId=self.pub_ip_info[PUBLIC_IP].id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2531_with_invalid_link_id(self):
        try:
            self.a1_r1.oapi.CreateNatService(PublicIpId='foo', SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2532_with_invalid_subnet_id(self):
        try:
            self.a1_r1.oapi.CreateNatService(PublicIpId=self.pub_ip_info[PUBLIC_IP].id, SubnetId='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2533_with_unknown_link_id(self):
        try:
            self.a1_r1.oapi.CreateNatService(PublicIpId='eipalloc-12345678', SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5025')

    def test_T2534_with_unknown_subnet_id(self):
        try:
            self.a1_r1.oapi.CreateNatService(PublicIpId=self.pub_ip_info[PUBLIC_IP].id, SubnetId='subnet-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5057')

    # TODO add tests:
    # - dry run failure
    # - invalid dry-run
    # - eip in use
    # - subnet wihtout IGW
    # - eip from another account
    # - subnet from anoher account
    # - 2 Nat in same subnet
