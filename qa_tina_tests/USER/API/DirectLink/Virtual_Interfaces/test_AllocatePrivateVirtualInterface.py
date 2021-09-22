
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest


@pytest.mark.region_directlink
@pytest.mark.region_admin
class Test_AllocatePrivateVirtualInterface(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.conn_id = None
        cls.quotas = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        cls.ret = None
        cls.known_error = False
        super(Test_AllocatePrivateVirtualInterface, cls).setup_class()
        try:
            cls.ret = cls.a1_r1.directlink.DescribeLocations()
            if cls.a1_r1.config.region.name == 'in-west-2' and len(cls.ret.response.locations) == 0:
                assert False, 'Remove known error'
            cls.location_code = cls.ret.response.locations[0].locationCode
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                if cls.a1_r1.config.region.name == 'in-west-2' and len(cls.ret.response.locations) == 0:
                    cls.known_error = True
                    return
                raise error1

    def setup_method(self, method):
        self.conn_id = None
        OscTinaTest.setup_method(self, method)
        if self.a1_r1.config.region.name == 'in-west-2' and len(self.ret.response.locations) == 0:
            self.known_error = True
            return
        ret = self.a1_r1.directlink.CreateConnection(location=self.location_code, bandwidth='1Gbps', connectionName=id_generator(prefix='dl_'))
        self.conn_id = ret.response.connectionId

    def teardown_method(self, method):
        try:
            if self.conn_id:
                self.a1_r1.intel.dl.connection.delete(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
        finally:
            OscTinaTest.teardown_method(self, method)

    def test_T4640_without_param(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        ret = None
        try:
            ret = self.a1_r1.directlink.AllocatePrivateVirtualInterface()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field connectionId is required")
        finally:
            if ret:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=ret.response.virtualInterfaceId)

    def test_T4637_without_allocation(self):
        ret = None
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        try:
            ret = self.a1_r1.directlink.AllocatePrivateVirtualInterface(connectionId=self.conn_id, ownerAccount=self.a1_r1.config.account.account_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field newPrivateVirtualInterfaceAllocation is required")
        finally:
            if ret:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=ret.response.virtualInterfaceId)

    def test_T4638_without_connection_id(self):
        ret = None
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        try:
            allocation = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
            ret = self.a1_r1.directlink.AllocatePrivateVirtualInterface(ownerAccount=self.a1_r1.config.account.account_id,
                                                                        newPrivateVirtualInterfaceAllocation=allocation)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field connectionId is required")
        finally:
            if ret:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=ret.response.virtualInterfaceId)

    def test_T4639_without_owner_account(self):
        ret = None
        allocation = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        try:
            ret = self.a1_r1.directlink.AllocatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                        newPrivateVirtualInterfaceAllocation=allocation)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field ownerAccount is required")
        finally:
            if ret:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=ret.response.virtualInterfaceId)

    def test_T1914_required_param(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        ret = None
        allocation = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        try:
            ret = self.a1_r1.directlink.AllocatePrivateVirtualInterface(
                connectionId=self.conn_id, newPrivateVirtualInterfaceAllocation=allocation,
                ownerAccount=self.a1_r1.config.account.account_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Connection is not available")
        finally:
            if ret:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=ret.response.virtualInterfaceId)

    def test_T4652_valid_connection_state(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        ret = None
        ret_activate = None
        allocation = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        try:
            ret_activate = self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            ret = self.a1_r1.directlink.AllocatePrivateVirtualInterface(
                connectionId=self.conn_id, newPrivateVirtualInterfaceAllocation=allocation,
                ownerAccount=self.a1_r1.config.account.account_id)
            assert ret.response.virtualInterfaceState == 'confirming'
            assert ret.response.asn == 11111
            assert ret.response.vlan == 2
            assert ret.response.ownerAccount == self.a1_r1.config.account.account_id
            assert ret.response.location == 'PAR5'
            assert ret.response.virtualInterfaceType == 'private'
            assert ret.response.virtualInterfaceId.startswith('dxvif-')
            assert ret.response.virtualInterfaceName == 'test'
        finally:
            if ret:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=ret.response.virtualInterfaceId)
            if ret_activate:
                self.a1_r1.intel.dl.connection.deactivate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)

    def test_T5737_with_extra_param(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        ret = None
        ret_activate = None
        allocation = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        try:
            ret_activate = self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            ret = self.a1_r1.directlink.AllocatePrivateVirtualInterface(
                connectionId=self.conn_id, newPrivateVirtualInterfaceAllocation=allocation,
                ownerAccount=self.a1_r1.config.account.account_id, Foo='Bar')
        finally:
            if ret:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=ret.response.virtualInterfaceId)
            if ret_activate:
                self.a1_r1.intel.dl.connection.deactivate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
