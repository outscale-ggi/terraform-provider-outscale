# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite, known_error


@pytest.mark.region_admin
class Test_CreatePrivateVirtualInterface(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.conn_id = None
        cls.QUOTAS = {'dl_connection_limit': 2, 'dl_interface_limit': 2}
        super(Test_CreatePrivateVirtualInterface, cls).setup_class()
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
            super(Test_CreatePrivateVirtualInterface, cls).teardown_class()

    @pytest.mark.region_directlink
    def test_T4658_invalid_connection_state(self):
        newPrivateVirtualInterface = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        try:
            self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                newPrivateVirtualInterface=newPrivateVirtualInterface)
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Connection is not available")

    @pytest.mark.region_directlink
    def test_T1910_required_param(self):
        newPrivateVirtualInterface = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        interface_info = None
        try:
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            interface_info = self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                                 newPrivateVirtualInterface=newPrivateVirtualInterface)
            assert interface_info.response.amazonAddress
            assert interface_info.response.asn == 11111
            assert interface_info.response.connectionId == self.conn_id
            assert interface_info.response.customerAddress
            assert interface_info.response.location == 'Par3'
            assert interface_info.response.ownerAccount == self.a1_r1.config.account.account_id
            assert interface_info.response.customerAddress
            assert interface_info.response.requestId
            assert interface_info.response.virtualInterfaceType == 'private'
            assert interface_info.response.virtualInterfaceId.startswith('dxvif-')
            assert interface_info.response.virtualInterfaceName == 'test'
            assert interface_info.response.virtualInterfaceState == 'confirming'
            assert interface_info.response.vlan == 2
        finally:
            self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info.response.virtualInterfaceId)

    @pytest.mark.region_directlink
    def test_T4659_without_newPrivateVirtualInterface(self):
        try:
            self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id)
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field newPrivateVirtualInterface is required")

    @pytest.mark.region_directlink
    def test_T4660_without_connectionId(self):
        try:
            self.a1_r1.directlink.CreatePrivateVirtualInterface()
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field connectionId is required")

    @pytest.mark.region_directlink
    def test_T4661_invalid_vlan(self):
        newPrivateVirtualInterface = {'asn': '11111', 'virtualInterfaceName': 'test', 'vlan': 's'}
        try:
            self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                newPrivateVirtualInterface=newPrivateVirtualInterface)
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Invalid type, newPrivateVirtualInterface.vlan must be an integer")

    @pytest.mark.region_directlink
    def test_T4662_invalid_asn(self):
        newPrivateVirtualInterface = {'asn': '11111', 'virtualInterfaceName': 'test', 'vlan': 1}
        try:
            self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                newPrivateVirtualInterface=newPrivateVirtualInterface)
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Invalid type, newPrivateVirtualInterface.asn must be an integer")

    @pytest.mark.region_directlink
    def test_T4663_invalid_virtualInterfaceName(self):
        newPrivateVirtualInterface = {'asn': '11111', 'virtualInterfaceName': 123, 'vlan': 1}
        try:
            self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                newPrivateVirtualInterface=newPrivateVirtualInterface)
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Invalid type, newPrivateVirtualInterface.virtualInterfaceName must be a string")

    @pytest.mark.region_directlink
    def test_T5367_with_existing_virtual_interface(self):
        newPrivateVirtualInterface = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
        interface_info = self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                             newPrivateVirtualInterface=newPrivateVirtualInterface)
        try:
            interface_info = self.a1_r1.directlink.CreatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                                 newPrivateVirtualInterface=newPrivateVirtualInterface)
        except OscApiException as error:
            if error.message == "Internal Error" and error.status_code == 500:
                known_error("TINA-4915" , "Virtual interface : Error message")
            assert False, 'remove known error code'
        finally:
            if interface_info:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=interface_info.response.virtualInterfaceId)
