import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, delete_instances
from qa_tina_tools.tools.tina.info_keys import SUBNET_ID, SUBNETS, INSTANCE_ID_LIST

NUM_STANDARD_EIPS = 2
NUM_VPC_EIPS = 10


class Test_UnlinkPublicIp(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.standard_eips = []
        cls.vpc_eips = []
        cls.vpc_info = None
        cls.inst_info = None
        cls.net1 = None
        cls.net2 = None
        try:
            super(Test_UnlinkPublicIp, cls).setup_class()
            cls.vpc_info = create_vpc(cls.a1_r1, nb_instance=2, nb_subnet=1, no_eip=True)
            cls.inst_info = create_instances(cls.a1_r1, nb=2, state='running')
            cls.net1 = cls.a1_r1.fcu.CreateNetworkInterface(SubnetId=cls.vpc_info[SUBNETS][0][SUBNET_ID]).response.networkInterface
            cls.net2 = cls.a1_r1.fcu.CreateNetworkInterface(SubnetId=cls.vpc_info[SUBNETS][0][SUBNET_ID]).response.networkInterface
            for _ in range(NUM_STANDARD_EIPS):
                cls.standard_eips.append(cls.a1_r1.fcu.AllocateAddress(Domain='standard').response)
            for _ in range(NUM_VPC_EIPS):
                cls.vpc_eips.append(cls.a1_r1.fcu.AllocateAddress(Domain='vpc').response)
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.net1:
                cls.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=cls.net1.networkInterfaceId)
            if cls.net2:
                cls.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=cls.net2.networkInterfaceId)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
            for eip in cls.standard_eips:
                cls.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)
            for eip in cls.vpc_eips:
                cls.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)
        finally:
            super(Test_UnlinkPublicIp, cls).teardown_class()

    def test_T2811_without_param(self):
        try:
            self.a1_r1.oapi.UnlinkPublicIp()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2812_with_both_compatible_params(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(VmId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=self.standard_eips[0].publicIp)
            self.a1_r1.oapi.UnlinkPublicIp(LinkPublicIpId=ret.response.LinkPublicIpId, PublicIp=self.standard_eips[0].publicIp)
            ret = None
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002')
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.standard_eips[0].publicIp)

    def test_T2813_with_both_incompatible_params(self):
        ret1 = None
        ret2 = None
        try:
            ret1 = self.a1_r1.oapi.LinkPublicIp(VmId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=self.standard_eips[0].publicIp)
            ret2 = self.a1_r1.oapi.LinkPublicIp(VmId=self.inst_info[INSTANCE_ID_LIST][1], PublicIp=self.standard_eips[1].publicIp)
            self.a1_r1.oapi.UnlinkPublicIp(LinkPublicIpId=ret2.response.LinkPublicIpId, PublicIp=self.standard_eips[0].publicIp)
            ret2 = None
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002')
        finally:
            if ret1:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.standard_eips[0].publicIp)
            if ret2:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.standard_eips[1].publicIp)

    def test_T2814_with_pub_inst_pub_ip(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(VmId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=self.standard_eips[0].publicIp)
            self.a1_r1.oapi.UnlinkPublicIp(PublicIp=self.standard_eips[0].publicIp)
            ret = None
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.standard_eips[0].publicIp)

    def test_T2815_with_pub_inst_link_id(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(VmId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=self.standard_eips[0].publicIp)
            self.a1_r1.oapi.UnlinkPublicIp(LinkPublicIpId=ret.response.LinkPublicIpId)
            ret = None
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.standard_eips[0].publicIp)

    def test_T2816_with_priv_inst_pub_ip(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(VmId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0], PublicIp=self.vpc_eips[0].publicIp)
            self.a1_r1.oapi.UnlinkPublicIp(PublicIp=self.vpc_eips[0].publicIp)
            ret = None
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[0].publicIp)

    def test_T2817_with_priv_inst_link_id(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(VmId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0], PublicIp=self.vpc_eips[0].publicIp)
            self.a1_r1.oapi.UnlinkPublicIp(LinkPublicIpId=ret.response.LinkPublicIpId)
            ret = None
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[0].publicIp)

    def test_T2818_with_ni_pub_ip(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(NicId=self.net1.networkInterfaceId, PublicIp=self.vpc_eips[2].publicIp)
            associationId = ret.response.LinkPublicIpId
            self.a1_r1.oapi.UnlinkPublicIp(PublicIp=self.vpc_eips[2].publicIp)
            associationId = None
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if associationId:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[2].publicIp)

    def test_T2819_with_ni_link_id(self):
        associationId = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(NicId=self.net1.networkInterfaceId, PublicIpId=self.vpc_eips[3].allocationId)
            associationId = ret.response.LinkPublicIpId
            self.a1_r1.oapi.UnlinkPublicIp(LinkPublicIpId=associationId)
            associationId = None
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if associationId:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[3].publicIp)

    def test_T3521_dry_run(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(VmId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=self.standard_eips[0].publicIp)
            ret = self.a1_r1.oapi.UnlinkPublicIp(PublicIp=self.standard_eips[0].publicIp, DryRun=True)
            assert_dry_run(ret)
            ret = None
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.standard_eips[0].publicIp)

    @pytest.mark.tag_sec_confidentiality
    def test_T3522_other_account(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(VmId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=self.standard_eips[0].publicIp)
            self.a2_r1.oapi.UnlinkPublicIp(PublicIp=self.standard_eips[0].publicIp)
            ret = None
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5025')
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.standard_eips[0].publicIp)
