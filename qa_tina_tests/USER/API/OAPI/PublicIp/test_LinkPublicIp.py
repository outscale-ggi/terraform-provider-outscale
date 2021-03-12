import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, delete_instances
from qa_tina_tools.tools.tina.info_keys import SUBNET_ID, SUBNETS, INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_addresses_state

NUM_STANDARD_EIPS = 1
NUM_VPC_EIPS = 10


class Test_LinkPublicIp(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.standard_eips = []
        cls.vpc_eips = []
        cls.vpc_info = None
        cls.inst_info = None
        cls.net1 = None
        cls.net2 = None
        try:
            super(Test_LinkPublicIp, cls).setup_class()
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
            super(Test_LinkPublicIp, cls).teardown_class()

    def test_T2765_with_pub_inst_pub_ip(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(VmId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=self.standard_eips[0].publicIp)
            assert ret.response.LinkPublicIpId and \
                isinstance(ret.response.LinkPublicIpId, str), "Missing/Incorrect response element 'LinkPublicIpId'."
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.standard_eips[0].publicIp)

    def test_T2766_with_priv_inst_pub_ip(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(VmId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0], PublicIp=self.vpc_eips[0].publicIp)
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[0].publicIp)

    def test_T2767_with_priv_inst_alloc_id(self):
        association_id = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(VmId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0], PublicIpId=self.vpc_eips[1].allocationId)
            association_id = ret.response.LinkPublicIpId
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if association_id:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[1].publicIp)

    def test_T2768_with_ni_pub_ip(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(NicId=self.net1.networkInterfaceId, PublicIp=self.vpc_eips[2].publicIp)
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[2].publicIp)

    def test_T2769_with_ni_alloc_id(self):
        association_id = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(NicId=self.net1.networkInterfaceId, PublicIpId=self.vpc_eips[3].allocationId)
            association_id = ret.response.LinkPublicIpId
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if association_id:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[3].publicIp)

    def test_T2770_no_element_pub_ip(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(PublicIp=self.vpc_eips[4].publicIp)
            assert False, 'Call should not have been successful'
        except Exception as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[4].publicIp)

    def test_T2771_no_element_alloc_id(self):
        association_id = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(PublicIpId=self.vpc_eips[5].allocationId)
            association_id = ret.response.LinkPublicIpId
            assert False, 'Call should not have been successful'
        except Exception as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000', None)
        finally:
            if association_id:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[5].publicIp)

    def test_T2772_with_priv_inst_empty_ni_alloc_id(self):
        association_id = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(VmId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                               NicId='',
                                               PublicIpId=self.vpc_eips[6].allocationId)
            association_id = ret.response.LinkPublicIpId
        # for debug purposes
        except Exception as error:
            assert_oapi_error(error, 400, 'MissingParameter', None)
        finally:
            if association_id:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[6].publicIp)

    def test_T2773_with_ni_empty_priv_inst_alloc_id(self):
        association_id = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(VmId='', NicId=self.net1.networkInterfaceId, PublicIpId=self.vpc_eips[7].allocationId)
            association_id = ret.response.LinkPublicIpId
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if association_id:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[7].publicIp)

    def test_T2774_reassoc_pub_none(self):
        eip = None
        try:
            eip = self.a1_r1.fcu.AllocateAddress(Domain='standard').response
            self.a1_r1.oapi.LinkPublicIp(VmId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=eip.publicIp)
            try:
                self.a1_r1.oapi.LinkPublicIp(VmId=self.inst_info[INSTANCE_ID_LIST][1], PublicIp=eip.publicIp, AllowRelink=None)
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')
        finally:
            if eip:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=eip.publicIp)
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)

    def test_T2775_reassoc_pub_false(self):
        eip = None
        try:
            eip = self.a1_r1.fcu.AllocateAddress(Domain='standard').response
            self.a1_r1.oapi.LinkPublicIp(VmId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=eip.publicIp)
            try:
                self.a1_r1.oapi.LinkPublicIp(VmId=self.inst_info[INSTANCE_ID_LIST][1], PublicIp=eip.publicIp, AllowRelink=False)
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 409, 'ResourceConflict', '9029')
        finally:
            if eip:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=eip.publicIp)
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)

    def test_T2776_reassoc_pub_true(self):
        eip = None
        ret = None
        try:
            eip = self.a1_r1.fcu.AllocateAddress(Domain='standard').response
            ret = self.a1_r1.oapi.LinkPublicIp(VmId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=eip.publicIp)
            ret = self.a1_r1.oapi.LinkPublicIp(VmId=self.inst_info[INSTANCE_ID_LIST][1], PublicIp=eip.publicIp, AllowRelink=True)
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=eip.publicIp)
            if eip:
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)

    def test_T2777_reassoc_private_none(self):
        eip = None
        assoc_id = None
        try:
            eip = self.a1_r1.fcu.AllocateAddress(Domain='vpc').response
            assoc_id = self.a1_r1.oapi.LinkPublicIp(VmId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                    PublicIpId=eip.allocationId).response.LinkPublicIpId
            try:
                self.a1_r1.oapi.LinkPublicIp(VmId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][1],
                                             PublicIpId=eip.allocationId,
                                             AllowRelink=None)
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if assoc_id:
                self.a1_r1.fcu.DisassociateAddress(AssociationId=assoc_id)
                wait_addresses_state(self.a1_r1, [eip.publicIp], state='available')
            if eip:
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)

    def test_T2778_reassoc_private_false(self):
        eip = None
        assoc_id = None
        try:
            eip = self.a1_r1.fcu.AllocateAddress(Domain='vpc').response
            assoc_id = self.a1_r1.oapi.LinkPublicIp(VmId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                    PublicIpId=eip.allocationId).response.LinkPublicIpId
            try:
                assoc_id = self.a1_r1.oapi.LinkPublicIp(VmId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][1],
                                                        PublicIpId=eip.allocationId, AllowRelink=False).response.LinkPublicIpId
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 409, 'ResourceConflict', '9029')
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if assoc_id:
                self.a1_r1.fcu.DisassociateAddress(AssociationId=assoc_id)
                wait_addresses_state(self.a1_r1, [eip.publicIp], state='available')
            if eip:
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)

    def test_T2779_reassoc_private_true(self):
        eip = None
        assoc_id = None
        try:
            eip = self.a1_r1.fcu.AllocateAddress(Domain='vpc').response
            assoc_id = self.a1_r1.oapi.LinkPublicIp(VmId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                    PublicIpId=eip.allocationId).response.LinkPublicIpId
            assoc_id = self.a1_r1.oapi.LinkPublicIp(VmId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][1],
                                                    PublicIpId=eip.allocationId, AllowRelink=True).response.LinkPublicIpId
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if assoc_id:
                self.a1_r1.fcu.DisassociateAddress(AssociationId=assoc_id)
                wait_addresses_state(self.a1_r1, [eip.publicIp], state='available')
            if eip:
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)

    def test_T3518_dry_run(self):
        ret = None
        try:
            ret = self.a1_r1.oapi.LinkPublicIp(VmId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0], PublicIp=self.vpc_eips[0].publicIp, DryRun=True)
            assert_dry_run(ret)
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[0].publicIp)

    @pytest.mark.tag_sec_confidentiality
    def test_T3519_other_account(self):
        ret = None
        try:
            ret = self.a2_r1.oapi.LinkPublicIp(VmId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0], PublicIp=self.vpc_eips[0].publicIp)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[0].publicIp)
