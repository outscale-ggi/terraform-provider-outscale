
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina import wait_tools


@pytest.mark.region_directlink
@pytest.mark.region_admin
class Test_CreatePrivateVirtualInterface(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.conn_id = None
        cls.quotas = {'dl_connection_limit': 10, 'dl_interface_limit': 10}
        cls.known_error = False
        super(Test_CreatePrivateVirtualInterface, cls).setup_class()
        try:
            ret = cls.a1_r1.directlink.DescribeLocations()
            if cls.a1_r1.config.region.name == 'in-west-2':
                if len(ret.response.locations) == 0:
                    cls.known_error = True
                    return
                assert False, 'remove known error'
            cls.location_code = ret.response.locations[0].locationCode
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    def setup_method(self, method):
        if self.known_error:
            return
        self.conn_id = None
        OscTinaTest.setup_method(self, method)
        ret = self.a1_r1.directlink.CreateConnection(location=self.location_code, bandwidth='1Gbps', connectionName=id_generator(prefix='dl_'))
        self.conn_id = ret.response.connectionId
        wait_tools.wait_direct_link_connection_state(self.a1_r1, self.conn_id, "pending")

    def teardown_method(self, method):
        try:
            if self.conn_id:
                self.a1_r1.intel.dl.connection.delete(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
        finally:
            OscTinaTest.teardown_method(self, method)

    def test_T4658_invalid_connection_state(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        interface_info = None
        interface = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        try:
            interface_info = self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                                 newPrivateVirtualInterface=interface)
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Connection is not available")
        finally:
            if interface_info:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info.response.virtualInterfaceId)

    def test_T1910_required_param(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        interface = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        interface_info = None
        try:
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            wait_tools.wait_direct_link_connection_state(self.a1_r1, self.conn_id, "available")
            interface_info = self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                                 newPrivateVirtualInterface=interface)
            assert interface_info.response.amazonAddress
            assert interface_info.response.asn == 11111
            assert interface_info.response.connectionId == self.conn_id
            assert interface_info.response.customerAddress
            assert interface_info.response.location == 'PAR5'
            assert interface_info.response.ownerAccount == self.a1_r1.config.account.account_id
            assert interface_info.response.customerAddress
            assert interface_info.response.requestId
            assert interface_info.response.virtualInterfaceType == 'private'
            assert interface_info.response.virtualInterfaceId.startswith('dxvif-')
            assert interface_info.response.virtualInterfaceName == 'test'
            assert interface_info.response.virtualInterfaceState == 'confirming'
            assert interface_info.response.vlan == 2
        finally:
            if interface_info:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info.response.virtualInterfaceId)

    def test_T4659_without_interface(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        interface_info = None
        try:
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            wait_tools.wait_direct_link_connection_state(self.a1_r1, self.conn_id, "available")
            interface_info = self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id)
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field newPrivateVirtualInterface is required")
        finally:
            if interface_info:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info.response.virtualInterfaceId)

    def test_T4660_without_connectionId(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        interface_info = None
        try:
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            wait_tools.wait_direct_link_connection_state(self.a1_r1, self.conn_id, "available")
            self.a1_r1.directlink.CreatePrivateVirtualInterface()
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field connectionId is required")
        finally:
            if interface_info:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info.response.virtualInterfaceId)

    def test_T4661_invalid_vlan(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        interface_info = None
        interface = {'asn': '11111', 'virtualInterfaceName': 'test', 'vlan': 's'}
        try:
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            wait_tools.wait_direct_link_connection_state(self.a1_r1, self.conn_id, "available")
            self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                newPrivateVirtualInterface=interface)
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException",
                         "Invalid type, newPrivateVirtualInterface.vlan must be an integer")
        finally:
            if interface_info:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info.response.virtualInterfaceId)

    def test_T4662_invalid_asn(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        interface_info = None
        interface = {'asn': '11111', 'virtualInterfaceName': 'test', 'vlan': 1}
        try:
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            wait_tools.wait_direct_link_connection_state(self.a1_r1, self.conn_id, "available")
            self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                newPrivateVirtualInterface=interface)
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException",
                         "Invalid type, newPrivateVirtualInterface.asn must be an integer")
        finally:
            if interface_info:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info.response.virtualInterfaceId)

    def test_T4663_invalid_virtualInterfaceName(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        interface_info = None
        interface = {'asn': '11111', 'virtualInterfaceName': 123, 'vlan': 1}
        try:
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            wait_tools.wait_direct_link_connection_state(self.a1_r1, self.conn_id, "available")
            self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                newPrivateVirtualInterface=interface)
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException",
                         "Invalid type, newPrivateVirtualInterface.virtualInterfaceName must be a string")
        finally:
            if interface_info:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info.response.virtualInterfaceId)

    def test_T5367_with_existing_virtual_interface(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        interface_info1 = None
        interface = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        try:
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            wait_tools.wait_direct_link_connection_state(self.a1_r1, self.conn_id, "available")
            interface_info1 = self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                                  newPrivateVirtualInterface=interface)
            interface_info2 = None
            try:
                interface_info2 = self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                                      newPrivateVirtualInterface=interface)
            except OscApiException as error:
                assert_error(error, 400, "DirectConnectClientException", "An Interface already exists with this VPN gateway: 2")
            finally:
                if interface_info2:
                    self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info2.response.virtualInterfaceId)
        finally:
            if interface_info1:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info1.response.virtualInterfaceId)

    def test_T5739_with_extra_param(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        interface = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        interface_info = None
        try:
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            wait_tools.wait_direct_link_connection_state(self.a1_r1, self.conn_id, "available")
            interface_info = self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                                 newPrivateVirtualInterface=interface,
                                                                                 Foo='Bar')
        finally:
            if interface_info:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info.response.virtualInterfaceId)
