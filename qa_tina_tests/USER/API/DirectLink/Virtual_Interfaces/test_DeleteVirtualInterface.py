
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_tina_tools.test_base import OscTinaTest


@pytest.mark.region_directlink
@pytest.mark.region_admin
class Test_DeleteVirtualInterface(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.conn_id = None
        cls.quotas = {'dl_connection_limit': 5, 'dl_interface_limit': 5}
        super(Test_DeleteVirtualInterface, cls).setup_class()
        cls.location = cls.a1_r1.directlink.DescribeLocations().response.locations[0].locationCode

    def setup_method(self, method):
        self.conn_id = None
        OscTinaTest.setup_method(self, method)
        self.conn_id = self.a1_r1.directlink.CreateConnection(location=self.location, bandwidth='1Gbps',
                                                              connectionName=id_generator(prefix='dl_')).response.connectionId
        self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)

    def teardown_method(self, method):
        try:
            if self.conn_id:
                self.a1_r1.intel.dl.connection.deactivate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
                self.a1_r1.intel.dl.connection.delete(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
        finally:
            OscTinaTest.teardown_method(self, method)

    def test_T1911_required_param(self):
        interface = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        interface_info = self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id, newPrivateVirtualInterface=interface)
        ret = self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info.response.virtualInterfaceId)
        assert ret.response.virtualInterfaceState == 'deleted'

    def test_T4664_without_param(self):
        try:
            self.a1_r1.directlink.DeleteVirtualInterface()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field virtualInterfaceId is required")

    def test_T4665_invalid_virtualInterfaceId(self):
        try:
            self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=self.conn_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Invalid ID received: {}. Expected format: dxvif-".format(self.conn_id))

    def test_T4666_non_existent_virtualInterfaceId(self):
        try:
            self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId='dxvif-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Virtual interface 'dxvif-12345678' does not exists.")

    def test_T5740_with_extra_param(self):
        interface = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        interface_info = self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id, newPrivateVirtualInterface=interface)
        ret = self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info.response.virtualInterfaceId, Foo='Bar')
        assert ret.response.virtualInterfaceState == 'deleted'
