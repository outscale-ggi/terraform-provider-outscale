

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.info_keys import SUBNETS, SUBNET_ID, PUBLIC_IP
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_public_ip
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, delete_public_ip
from qa_tina_tools.tools.tina.wait_tools import wait_nat_gateways_state


class Test_DeleteNatService(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteNatService, cls).setup_class()
        cls.vpc_info = None
        cls.pub_ip_info = None
        cls.nat_id = None
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, default_rtb=True, no_ping=True)
            cls.pub_ip_info = create_public_ip(cls.a1_r1, domain='vpc')
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.pub_ip_info:
                delete_public_ip(cls.a1_r1, cls.pub_ip_info)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_DeleteNatService, cls).teardown_class()

    def test_T2535_dry_run(self):
        nat_id = None
        try:
            ret = self.a1_r1.oapi.CreateNatService(PublicIpId=self.pub_ip_info[PUBLIC_IP].id, SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            nat_id = ret.response.NatService.NatServiceId
            ret = self.a1_r1.oapi.DeleteNatService(NatServiceId=nat_id, DryRun=True)
            assert_dry_run(ret)
        finally:
            if nat_id:
                self.a1_r1.oapi.DeleteNatService(NatServiceId=nat_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[nat_id], state='deleted')

    def test_T2536_valid_id(self):
        nat_id = None
        try:
            ret = self.a1_r1.oapi.CreateNatService(PublicIpId=self.pub_ip_info[PUBLIC_IP].id, SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            nat_id = ret.response.NatService.NatServiceId
            self.a1_r1.oapi.DeleteNatService(NatServiceId=nat_id)
            nat_id = None
        finally:
            if nat_id:
                self.a1_r1.oapi.DeleteNatService(NatServiceId=nat_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[nat_id], state='deleted')

    def test_T2537_no_id(self):
        try:
            self.a1_r1.oapi.DeleteNatService()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2538_invalid_id(self):
        try:
            self.a1_r1.oapi.DeleteNatService(NatServiceId='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2539_unknown_id(self):
        try:
            self.a1_r1.oapi.DeleteNatService(NatServiceId='nat-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5032')

    @pytest.mark.tag_sec_confidentiality
    def test_T2540_with_id_from_another_account(self):
        nat_id = None
        try:
            ret = self.a1_r1.oapi.CreateNatService(PublicIpId=self.pub_ip_info[PUBLIC_IP].id, SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            nat_id = ret.response.NatService.NatServiceId
            self.a1_r1.oapi.DeleteNatService(NatServiceId=nat_id)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5032')
        finally:
            if nat_id:
                self.a1_r1.oapi.DeleteNatService(NatServiceId=nat_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[nat_id], state='deleted')

    def test_T3467_invalid_dry_run(self):
        nat_id = None
        try:
            ret = self.a1_r1.oapi.CreateNatService(PublicIpId=self.pub_ip_info[PUBLIC_IP].id, SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            nat_id = ret.response.NatService.NatServiceId
            ret = self.a1_r1.oapi.DeleteNatService(DryRun=True)
            assert_dry_run(ret)
        except OscApiException as err:
            assert_oapi_error(err, 400, 'MissingParameter', '7000')
        finally:
            if nat_id:
                self.a1_r1.oapi.DeleteNatService(NatServiceId=nat_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[nat_id], state='deleted')
