
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, delete_instances
from qa_tina_tools.tools.tina.info_keys import SUBNET_ID, SUBNETS, INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_addresses_state

NUM_STANDARD_EIPS = 1
NUM_VPC_EIPS = 10


class Test_AssociateAddress(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.standard_eips = []
        cls.vpc_eips = []
        cls.vpc_info = None
        cls.inst_info = None
        cls.net1 = None
        cls.net2 = None
        try:
            super(Test_AssociateAddress, cls).setup_class()
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
            finally:
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
            super(Test_AssociateAddress, cls).teardown_class()

    def test_T1601_with_pub_inst_pub_ip(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.AssociateAddress(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=self.standard_eips[0].publicIp)
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.standard_eips[0].publicIp)

    def test_T1603_with_priv_inst_pub_ip(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.AssociateAddress(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0], PublicIp=self.vpc_eips[0].publicIp)
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[0].publicIp)

    def test_T1604_with_priv_inst_alloc_id(self):
        association_id = None
        try:
            ret = self.a1_r1.fcu.AssociateAddress(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                  AllocationId=self.vpc_eips[1].allocationId)
            association_id = ret.response.associationId
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if association_id:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[1].publicIp)

    def test_T1605_with_ni_pub_ip(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.AssociateAddress(NetworkInterfaceId=self.net1.networkInterfaceId, PublicIp=self.vpc_eips[2].publicIp)
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[2].publicIp)

    def test_T1606_with_ni_alloc_id(self):
        association_id = None
        try:
            ret = self.a1_r1.fcu.AssociateAddress(NetworkInterfaceId=self.net1.networkInterfaceId, AllocationId=self.vpc_eips[3].allocationId)
            association_id = ret.response.associationId
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if association_id:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[3].publicIp)

    def test_T1607_no_element_pub_ip(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.AssociateAddress(PublicIp=self.vpc_eips[4].publicIp)
            assert False, 'Call should not have been successful'
        except Exception as error:
            assert_error(error, 400, 'OWS.Error', 'Request is not valid.')
        finally:
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[4].publicIp)

    def test_T1608_no_element_alloc_id(self):
        association_id = None
        try:
            ret = self.a1_r1.fcu.AssociateAddress(AllocationId=self.vpc_eips[5].allocationId)
            association_id = ret.response.associationId
            assert False, 'Call should not have been successful'
        except Exception as error:
            assert_error(error, 400, 'OWS.Error', 'Request is not valid.')
        finally:
            if association_id:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[5].publicIp)

    def test_T1609_with_priv_inst_empty_ni_alloc_id(self):
        association_id = None
        try:
            ret = self.a1_r1.fcu.AssociateAddress(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                  NetworkInterfaceId='', AllocationId=self.vpc_eips[6].allocationId)
            association_id = ret.response.associationId
        # for debug purposes
        except Exception as error:
            assert_error(error, 400, 'MissingParameter', 'Insufficient parameters provided out of: Vm, nic. Expected at least: 1')
        finally:
            if association_id:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[6].publicIp)

    def test_T1610_with_ni_empty_priv_inst_alloc_id(self):
        association_id = None
        try:
            ret = self.a1_r1.fcu.AssociateAddress(InstanceId='',
                                                  NetworkInterfaceId=self.net1.networkInterfaceId, AllocationId=self.vpc_eips[7].allocationId)
            association_id = ret.response.associationId
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if association_id:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eips[7].publicIp)

    def test_T1688_reassoc_pub_none(self):
        eip = None
        try:
            eip = self.a1_r1.fcu.AllocateAddress(Domain='standard').response
            self.a1_r1.fcu.AssociateAddress(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=eip.publicIp)
            try:
                self.a1_r1.fcu.AssociateAddress(InstanceId=self.inst_info[INSTANCE_ID_LIST][1], PublicIp=eip.publicIp, AllowReassociation=None)
            except OscApiException as error:
                raise error
        finally:
            if eip:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=eip.publicIp)
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)

    def test_T1615_reassoc_pub_false(self):
        eip = None
        try:
            eip = self.a1_r1.fcu.AllocateAddress(Domain='standard').response
            self.a1_r1.fcu.AssociateAddress(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=eip.publicIp)
            try:
                self.a1_r1.fcu.AssociateAddress(InstanceId=self.inst_info[INSTANCE_ID_LIST][1], PublicIp=eip.publicIp, AllowReassociation=False)
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'InvalidIPAddress.InUse', 'Address is in use: ' + eip.publicIp)
        finally:
            if eip:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=eip.publicIp)
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)

    def test_T1616_reassoc_pub_true(self):
        eip = None
        try:
            eip = self.a1_r1.fcu.AllocateAddress(Domain='standard').response
            self.a1_r1.fcu.AssociateAddress(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=eip.publicIp)
            self.a1_r1.fcu.AssociateAddress(InstanceId=self.inst_info[INSTANCE_ID_LIST][1], PublicIp=eip.publicIp, AllowReassociation=True)
        finally:
            if eip:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=eip.publicIp)
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)

    def test_T1689_reassoc_private_none(self):
        eip = None
        assoc_id = None
        try:
            eip = self.a1_r1.fcu.AllocateAddress(Domain='vpc').response
            assoc_id = self.a1_r1.fcu.AssociateAddress(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                       AllocationId=eip.allocationId).response.associationId
            try:
                assoc_id = self.a1_r1.fcu.AssociateAddress(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][1],
                                                           AllocationId=eip.allocationId, AllowReassociation=None).response.associationId
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                if error.status_code == 400 and error.error_code == 'InvalidIPAddress.InUse':
                    pass
                else:
                    raise error
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if assoc_id:
                self.a1_r1.fcu.DisassociateAddress(AssociationId=assoc_id)
                wait_addresses_state(self.a1_r1, [eip.publicIp], state='available')
            if eip:
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)

    def test_T1617_reassoc_private_false(self):
        eip = None
        assoc_id = None
        try:
            eip = self.a1_r1.fcu.AllocateAddress(Domain='vpc').response
            assoc_id = self.a1_r1.fcu.AssociateAddress(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                       AllocationId=eip.allocationId).response.associationId
            try:
                assoc_id = self.a1_r1.fcu.AssociateAddress(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][1],
                                                           AllocationId=eip.allocationId, AllowReassociation=False).response.associationId
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                if error.status_code == 400 and error.error_code == 'InvalidIPAddress.InUse':
                    pass
                else:
                    raise error
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if assoc_id:
                self.a1_r1.fcu.DisassociateAddress(AssociationId=assoc_id)
                wait_addresses_state(self.a1_r1, [eip.publicIp], state='available')
            if eip:
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)

    def test_T1618_reassoc_private_true(self):
        eip = None
        assoc_id = None
        try:
            eip = self.a1_r1.fcu.AllocateAddress(Domain='vpc').response
            assoc_id = self.a1_r1.fcu.AssociateAddress(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                       AllocationId=eip.allocationId).response.associationId
            assoc_id = self.a1_r1.fcu.AssociateAddress(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][1],
                                                       AllocationId=eip.allocationId, AllowReassociation=True).response.associationId
        # for debug purposes
        except Exception as error:
            raise error
        finally:
            if assoc_id:
                self.a1_r1.fcu.DisassociateAddress(AssociationId=assoc_id)
                wait_addresses_state(self.a1_r1, [eip.publicIp], state='available')
            if eip:
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)
