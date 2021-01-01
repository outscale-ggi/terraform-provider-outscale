# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import id_generator
import pytest


@pytest.mark.region_admin
class Test_DescribeConnections(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        cls.conn_id = None
        cls.connectionName = id_generator(prefix='dl_')
        super(Test_DescribeConnections, cls).setup_class()
        ret = cls.a1_r1.directlink.DescribeLocations()
        cls.location = ret.response.locations[0].locationCode
        ret = cls.a1_r1.directlink.CreateConnection(location=cls.location, bandwidth='1Gbps', connectionName=cls.connectionName)
        cls.conn_id = ret.response.connectionId

    @classmethod
    def teardown_class(cls):
        try:
            if cls.conn_id:
                cls.a1_r1.intel.dl.connection.delete(owner=cls.a1_r1.config.account.account_id, connection_id=cls.conn_id)
        finally:
            super(Test_DescribeConnections, cls).teardown_class()

    @pytest.mark.region_directlink
    def test_T1909_without_param(self):
        ret = self.a1_r1.directlink.DescribeConnections()
        assert len(ret.response.connections) == 1
        assert ret.response.connections[0].bandwidth == '1Gbps'
        assert ret.response.connections[0].connectionName == self.connectionName
        assert ret.response.connections[0].connectionState == 'pending'
        assert ret.response.connections[0].location == self.location
        assert ret.response.connections[0].ownerAccount == self.a1_r1.config.account.account_id
        assert ret.response.connections[0].region == self.a1_r1.config.region.name
        assert ret.response.connections[0].connectionId.startswith('dxcon-')

    @pytest.mark.region_directlink
    def test_T4650_with_valid_param(self):
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

    @pytest.mark.region_directlink
    def test_T4651_without_invalid_connectionId(self):
        ret = self.a1_r1.directlink.DescribeConnections(connectionId='dxcon-12435698')
        assert len(ret.response.connections) == 0
