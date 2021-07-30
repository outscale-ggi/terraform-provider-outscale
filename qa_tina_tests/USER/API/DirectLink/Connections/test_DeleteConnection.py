
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_tina_tools.test_base import OscTinaTest


@pytest.mark.region_admin
@pytest.mark.region_directlink
class Test_DeleteConnection(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        cls.conn_id = None
        super(Test_DeleteConnection, cls).setup_class()
        ret = cls.a1_r1.directlink.DescribeLocations()
        cls.location = ret.response.locations[0].locationCode

    def setup_method(self, method):
        OscTinaTest.setup_method(self, method)
        ret = self.a1_r1.directlink.CreateConnection(location=self.location, bandwidth='1Gbps', connectionName=id_generator(prefix='dl_'))
        self.conn_id = ret.response.connectionId

    def teardown_method(self, method):
        try:
            if self.conn_id:
                ret = self.a1_r1.directlink.DescribeConnections(connectionId=self.conn_id)
                if ret.response.connections and ret.response.connections[0].connectionState != 'deleted':
                    self.a1_r1.intel.dl.connection.delete(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
        finally:
            OscTinaTest.teardown_method(self, method)

    def test_T587_valid_connection_id(self):
        self.a1_r1.directlink.DeleteConnection(connectionId=self.conn_id)

    def test_T585_invalid_connection_id(self):
        try:
            self.a1_r1.directlink.DeleteConnection(connectionId='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'DirectConnectClientException', "Connection 'foo' does not exists.")

    def test_T584_no_param(self):
        try:
            self.a1_r1.directlink.DeleteConnection()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'DirectConnectClientException', 'Field connectionId is required')

    def test_T4649_other_account(self):
        try:
            self.a2_r1.directlink.DeleteConnection(connectionId=self.conn_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'DirectConnectClientException', "Connection '{}' does not exists.".format(self.conn_id))

    def test_T5734_with_extra_param(self):
        self.a1_r1.directlink.DeleteConnection(connectionId=self.conn_id, Foo='Bar')
