
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from specs.check_tools import check_directlink_error
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest


@pytest.mark.region_admin
@pytest.mark.region_directlink
class Test_DeleteConnection(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        cls.conn_id = None
        cls.known_error = False
        super(Test_DeleteConnection, cls).setup_class()
        try:
            ret = cls.a1_r1.directlink.DescribeLocations()
            if cls.a1_r1.config.region.name == 'in-west-2':
                if len(ret.response.locations) == 0:
                    cls.known_error = True
                    return
                assert False, 'remove known error'
            cls.location = ret.response.locations[0].locationCode
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    def setup_method(self, method):
        OscTinaTest.setup_method(self, method)
        if self.known_error:
            return
        ret = self.a1_r1.directlink.CreateConnection(location=self.location, bandwidth='1Gbps', connectionName=misc.id_generator(prefix='dl_'))
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
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        self.a1_r1.directlink.DeleteConnection(connectionId=self.conn_id)

    def test_T585_invalid_connection_id(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        try:
            self.a1_r1.directlink.DeleteConnection(connectionId='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_directlink_error(error, 4104, invalid='foo', prefixes='dxcon-')

    def test_T584_no_param(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        try:
            self.a1_r1.directlink.DeleteConnection()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_directlink_error(error, 7000, missing_parameters='connectionId')

    def test_T4649_other_account(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        try:
            self.a2_r1.directlink.DeleteConnection(connectionId=self.conn_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_directlink_error(error, 5072, id=self.conn_id)

    def test_T5734_with_extra_param(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        self.a1_r1.directlink.DeleteConnection(connectionId=self.conn_id, Foo='Bar')
