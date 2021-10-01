
import pytest

from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest


@pytest.mark.region_directlink
@pytest.mark.region_admin
class Test_DescribeConnections(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        cls.conn_id = None
        cls.connectionName = id_generator(prefix='dl_')
        cls.known_error = False
        super(Test_DescribeConnections, cls).setup_class()
        try:
            ret = cls.a1_r1.directlink.DescribeLocations()
            if cls.a1_r1.config.region.name == 'in-west-2':
                if len(ret.response.locations) == 0:
                    cls.known_error = True
                    return
                assert False, 'remove known error'
            cls.location = ret.response.locations[0].locationCode
            ret = cls.a1_r1.directlink.CreateConnection(location=cls.location, bandwidth='1Gbps', connectionName=cls.connectionName)
            cls.conn_id = ret.response.connectionId
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1


    @classmethod
    def teardown_class(cls):
        try:
            if cls.conn_id:
                cls.a1_r1.intel.dl.connection.delete(owner=cls.a1_r1.config.account.account_id, connection_id=cls.conn_id)
        finally:
            super(Test_DescribeConnections, cls).teardown_class()

    def test_T1909_without_param(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        ret = self.a1_r1.directlink.DescribeConnections()
        assert len(ret.response.connections) == 1
        assert ret.response.connections[0].bandwidth == '1Gbps'
        assert ret.response.connections[0].connectionName == self.connectionName
        assert ret.response.connections[0].connectionState == 'pending'
        assert ret.response.connections[0].location == self.location
        assert ret.response.connections[0].ownerAccount == self.a1_r1.config.account.account_id
        assert ret.response.connections[0].region == self.a1_r1.config.region.name
        assert ret.response.connections[0].connectionId.startswith('dxcon-')

    def test_T4650_with_valid_param(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        ret = self.a1_r1.directlink.DescribeConnections(connectionId=self.conn_id)
        assert len(ret.response.connections) == 1
        assert ret.response.connections[0].bandwidth == '1Gbps'
        assert ret.response.connections[0].connectionName == self.connectionName
        assert ret.response.connections[0].connectionState == 'pending'
        assert ret.response.connections[0].location == self.location
        assert ret.response.connections[0].ownerAccount == self.a1_r1.config.account.account_id
        assert ret.response.connections[0].region == self.a1_r1.config.region.name
        assert ret.response.connections[0].connectionId.startswith('dxcon-')
        assert ret.response.connections[0].connectionId == self.conn_id

    def test_T4651_without_invalid_connectionId(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        ret = self.a1_r1.directlink.DescribeConnections(connectionId='dxcon-12435698')
        assert len(ret.response.connections) == 0

    def test_T5735_with_extra_param(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        self.a1_r1.directlink.DescribeConnections(Foo='Bar')
