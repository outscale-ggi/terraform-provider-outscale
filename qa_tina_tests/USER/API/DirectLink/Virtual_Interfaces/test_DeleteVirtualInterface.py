# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

import pytest
from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.misc import id_generator, assert_error
from osc_common.exceptions.osc_exceptions import OscApiException


@pytest.mark.region_admin
class Test_DeleteVirtualInterface(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.conn_id = None
        cls.QUOTAS = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        super(Test_DeleteVirtualInterface, cls).setup_class()
        ret = cls.a1_r1.directlink.DescribeLocations()
        ret = cls.a1_r1.directlink.CreateConnection(location=ret.response.locations[0].locationCode,
                                                    bandwidth='1Gbps', connectionName=id_generator(prefix='dl_'))
        cls.conn_id = ret.response.connectionId

    @classmethod
    def teardown_class(cls):
        try:
            if cls.conn_id:
                cls.a1_r1.intel.dl.connection.delete(owner=cls.a1_r1.config.account.account_id, connection_id=cls.conn_id)
        finally:
            super(Test_DeleteVirtualInterface, cls).teardown_class()

    @pytest.mark.region_admin
    @pytest.mark.region_directlink
    def test_T1911_required_param(self):
        newPrivateVirtualInterface = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        interface_info = None
        try:
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            interface_info = self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                                 newPrivateVirtualInterface=newPrivateVirtualInterface)
            ret = self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info.response.virtualInterfaceId)
            assert ret.response.virtualInterfaceState == 'deleted'
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field virtualInterfaceId is required")

    @pytest.mark.region_directlink
    def test_T4664_without_param(self):
        try:
            self.a1_r1.directlink.DeleteVirtualInterface()
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field virtualInterfaceId is required")

    @pytest.mark.region_directlink
    def test_T4665_invalid_virtualInterfaceId(self):
        try:
            self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=self.conn_id)
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Invalid ID received: {}. Expected format: dxvif-".format(self.conn_id))

    @pytest.mark.region_directlink
    def test_T4666_inexistante_virtualInterfaceId(self):
        try:
            self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId='dxvif-12345678')
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Virtual interface 'dxvif-12345678' does not exists.")
