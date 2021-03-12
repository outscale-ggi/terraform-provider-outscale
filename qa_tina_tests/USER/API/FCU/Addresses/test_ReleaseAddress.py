import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, delete_instances
from qa_tina_tools.tools.tina.info_keys import SUBNET_ID, SUBNETS, INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_network_interfaces_state


class Test_ReleaseAddress(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        cls.ip_list = None
        cls.ip_account2 = None
        cls.alloc_id_account2 = None
        super(Test_ReleaseAddress, cls).setup_class()
        try:
            cls.inst_info = create_instances(cls.a1_r1)
        except Exception:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_ReleaseAddress, cls).teardown_class()

    def setup_method(self, method):
        super(Test_ReleaseAddress, self).setup_method(method)
        try:
            self.ip_list = []
            for _ in range(2):
                ret = self.conns[0].fcu.AllocateAddress()
                ip = ret.response.publicIp
                ret = self.conns[0].fcu.DescribeAddresses(PublicIp=ip)
                alloc_id = ret.response.addressesSet[0].allocationId
                self.ip_list.append({'ip': ip, 'alloc_id': alloc_id})
            ret = self.conns[0].fcu.AssociateAddress(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=self.ip_list[0]['ip'])
            ret = self.conns[1].fcu.AllocateAddress()
            self.ip_account2 = ret.response.publicIp
            ret = self.conns[1].fcu.DescribeAddresses(PublicIp=self.ip_account2)
            self.alloc_id_account2 = ret.response.addressesSet[0].allocationId
        except Exception as error:
            try:
                self.teardown_method(method)
            finally:
                raise error

    def teardown_method(self, method):
        try:
            for i in range(len(self.conns)):
                ret = self.conns[i].fcu.DescribeAddresses()
                if ret.response.addressesSet:
                    for k in ret.response.addressesSet:
                        if k.instanceId:
                            self.a1_r1.fcu.DisassociateAddress(AssociationId=k.associationId)
                        self.conns[i].fcu.ReleaseAddress(PublicIp=k.publicIp)
        finally:
            super(Test_ReleaseAddress, self).teardown_method(method)

    def test_T308_without_param(self):
        try:
            self.conns[0].fcu.ReleaseAddress()
            pytest.fail("Should not have been able to call method without parameter")
        except OscApiException as error:
            assert error.status_code == 400
            assert error.message == 'Request is not valid.'

    def test_T312_with_allocationid_from_another_account(self):
        try:
            self.conns[0].fcu.ReleaseAddress(AllocationId=self.alloc_id_account2)
            pytest.fail("Should not have been able to release allocation id from another qccount")
        except OscApiException as error:
            assert error.status_code == 400
            assert error.message == "The allocation ID '{}' does not exist".format(self.alloc_id_account2)

    def test_T316_with_publicip_from_another_account(self):
        try:
            self.conns[0].fcu.ReleaseAddress(PublicIp=self.ip_account2)
            pytest.fail("Should not have been able to release public ip from another qccount")
        except OscApiException as error:
            assert error.status_code == 400
            assert error.message == "The address '%s' does not belong to you." % self.ip_account2

    def test_T309_with_valid_allocationid(self):
        self.conns[0].fcu.ReleaseAddress(AllocationId=self.ip_list[1]['alloc_id'])

    def test_T311_with_allocationid_in_use_public_cloud(self):
        self.conns[0].fcu.ReleaseAddress(AllocationId=self.ip_list[0]['alloc_id'])

    def test_T1800_with_allocationid_in_use_private_cloud(self):
        vpc_info = create_vpc(self.a1_r1, nb_instance=1, nb_subnet=1, no_eip=True)
        eip = self.a1_r1.fcu.AllocateAddress(Domain='vpc').response
        self.a1_r1.fcu.AssociateAddress(InstanceId=vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                        PublicIp=eip.publicIp)
        try:
            self.conns[0].fcu.ReleaseAddress(AllocationId=eip.allocationId)
            pytest.fail("Should not have been able to release in use allocation")
        except OscApiException as error:
            assert_error(error, 400, 'InvalidIPAddress.InUse', 'Address is in use: {}'.format(eip.publicIp))
        finally:
            self.a1_r1.fcu.DisassociateAddress(PublicIp=eip.publicIp)
            self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)
            delete_vpc(self.a1_r1, vpc_info)

    def test_T1801_with_allocationid_in_use_fni(self):
        knownerror = False
        vpc_info = create_vpc(self.a1_r1, nb_instance=1, nb_subnet=1)
        fni = self.a1_r1.fcu.CreateNetworkInterface(SubnetId=vpc_info[SUBNETS][0][SUBNET_ID]).response.networkInterface
        eip = self.a1_r1.fcu.AllocateAddress(Domain='vpc').response
        self.a1_r1.fcu.AssociateAddress(NetworkInterfaceId=fni.networkInterfaceId,
                                        PublicIp=eip.publicIp)
        att_id = self.a1_r1.fcu.AttachNetworkInterface(InstanceId=vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                    NetworkInterfaceId=fni.networkInterfaceId, DeviceIndex=1).response.attachmentId
        try:
            self.a1_r1.fcu.ReleaseAddress(AllocationId=eip.allocationId)
            pytest.fail("Should not have been able to release in use allocation")
        except OscApiException as error:
            assert_error(error, 400, 'InvalidIPAddress.InUse', 'Address is in use: {}'.format(eip.publicIp))
        finally:
            if not knownerror:
                self.a1_r1.fcu.DetachNetworkInterface(AttachmentId=att_id)
                wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni.networkInterfaceId], state='available')
                self.a1_r1.fcu.DisassociateAddress(PublicIp=eip.publicIp)
                self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)
            self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=fni.networkInterfaceId)
            delete_vpc(self.a1_r1, vpc_info)

    def test_T310_with_invalid_allocationid(self):
        try:
            self.conns[0].fcu.ReleaseAddress(AllocationId='toto')
            pytest.fail("Should not have been able to release invalid allocation id")
        except OscApiException as error:
            assert error.status_code == 400
            assert error.message == "The allocation ID 'toto' does not exist"

    def test_T313_with_valid_publicip(self):
        self.conns[0].fcu.ReleaseAddress(PublicIp=self.ip_list[1]['ip'])

    def test_T314_with_invalid_publicip(self):
        try:
            self.conns[0].fcu.ReleaseAddress(PublicIp='toto')
            pytest.fail("Should not have been able to release invalid public ip")
        except OscApiException as error:
            assert error.status_code == 400
            assert error.message == "Invalid IPv4 address: toto"

    def test_T315_with_publicip_in_use(self):
        self.conns[0].fcu.ReleaseAddress(PublicIp=self.ip_list[0]['ip'])

    def test_T317_with_valid_allocationid_and_publicip(self):
        self.conns[0].fcu.ReleaseAddress(PublicIp=self.ip_list[1]['ip'], AllocationId=self.ip_list[1]['alloc_id'])

    def test_T318_with_invalid_allocationid_and_publicip(self):
        self.conns[0].fcu.ReleaseAddress(PublicIp=self.ip_list[1]['ip'], AllocationId=self.ip_list[0]['alloc_id'])

    def test_T319_with_invalid_param(self):
        self.conns[0].fcu.ReleaseAddress(PublicIp=self.ip_list[1]['ip'], toto='toto')
