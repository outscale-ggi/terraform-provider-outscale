# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_CreateConnection(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        super(Test_CreateConnection, cls).setup_class()
        ret = cls.a1_r1.directlink.DescribeLocations()
        cls.location = ret.response.locations[0].locationCode

    @classmethod
    def teardown_class(cls):
        super(Test_CreateConnection, cls).teardown_class()

    @pytest.mark.region_directlink
    def test_T1908_required_param(self):
        conn_id = None
        connectionName = id_generator(prefix='dl_')
        try:
            ret = self.a1_r1.directlink.CreateConnection(location=self.location, bandwidth='1Gbps', connectionName=connectionName)
            conn_id = ret.response.connectionId
            assert ret.response.bandwidth == '1Gbps'
            assert ret.response.connectionName == connectionName
            assert ret.response.connectionState == 'requested'
            assert ret.response.location == self.location
            assert ret.response.ownerAccount == self.a1_r1.config.account.account_id
            assert ret.response.region == self.a1_r1.config.region.name
            assert ret.response.connectionId.startswith('dxcon-')
        finally:
            if conn_id:
                self.a1_r1.directlink.DeleteConnection(connectionId=conn_id)

    @pytest.mark.region_directlink
    def test_T4467_without_bandwidth(self):
        try:
            self.a1_r1.directlink.CreateConnection(location=self.location, connectionName=id_generator(prefix='dl_'))
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'DirectConnectClientException', 'Field bandwidth is required')

    @pytest.mark.region_directlink
    def test_T4468_without_name(self):
        try:
            self.a1_r1.directlink.CreateConnection(location=self.location, bandwidth='1Gbps')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'DirectConnectClientException', 'Field connectionName is required')

    @pytest.mark.region_directlink
    def test_T4469_without_location(self):
        try:
            self.a1_r1.directlink.CreateConnection(bandwidth='1Gbps', connectionName=id_generator(prefix='dl_'))
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'DirectConnectClientException', 'Field location is required')

    @pytest.mark.region_directlink
    def test_T4470_with_invalid_bandwidth(self):
        try:
            self.a1_r1.directlink.CreateConnection(location=self.location, bandwidth='foo', connectionName=id_generator(prefix='dl_'))
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'DirectConnectClientException', 'Invalid interface speed: foo')

    @pytest.mark.region_directlink
    def test_T4471_with_invalid_location(self):
        try:
            self.a1_r1.directlink.CreateConnection(location='foo', bandwidth='1Gbps', connectionName=id_generator(prefix='dl_'))
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'DirectConnectClientException', "Location 'foo' is invalid.")
