# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

import pytest
from qa_test_tools.test_base import OscTestSuite
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator


@pytest.mark.region_admin
class Test_AllocatePrivateVirtualInterface(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.conn_id = None
        cls.QUOTAS = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        super(Test_AllocatePrivateVirtualInterface, cls).setup_class()
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
            super(Test_AllocatePrivateVirtualInterface, cls).teardown_class()

    @pytest.mark.region_directlink
    def test_T4640_without_param(self):
        ret = None
        try:
            ret = self.a1_r1.directlink.AllocatePrivateVirtualInterface()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field connectionId is required")
        finally:
            if ret:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=ret.response.virtualInterfaceId)

    @pytest.mark.region_directlink
    def test_T4637_without_newPrivateVirtualInterfaceAllocation(self):
        ret = None
        try:
            ret = self.a1_r1.directlink.AllocatePrivateVirtualInterface(connectionId=self.conn_id, ownerAccount=self.a1_r1.config.account.account_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field newPrivateVirtualInterfaceAllocation is required")
        finally:
            if ret:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=ret.response.virtualInterfaceId)

    @pytest.mark.region_directlink
    def test_T4638_without_connectionId(self):
        ret = None
        try:
            newPrivateVirtualInterfaceAllocation = {'asn': '11111', 'virtualInterfaceName': 'test', 'vlan': 's'}
            ret = self.a1_r1.directlink.AllocatePrivateVirtualInterface(ownerAccount=self.a1_r1.config.account.account_id,
                                                                        newPrivateVirtualInterfaceAllocation=newPrivateVirtualInterfaceAllocation)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field connectionId is required")
        finally:
            if ret:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=ret.response.virtualInterfaceId)

    @pytest.mark.region_directlink
    def test_T4639_without_ownerAccount(self):
        ret = None
        newPrivateVirtualInterfaceAllocation = {'asn': '11111', 'virtualInterfaceName': 'test', 'vlan': 's'}
        try:
            ret = self.a1_r1.directlink.AllocatePrivateVirtualInterface(connectionId=self.conn_id,
                                                                        newPrivateVirtualInterfaceAllocation=newPrivateVirtualInterfaceAllocation)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Field ownerAccount is required")
        finally:
            if ret:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=ret.response.virtualInterfaceId)

    @pytest.mark.region_directlink
    def test_T1914_required_param(self):
        ret = None
        newPrivateVirtualInterfaceAllocation = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        try:
            ret = self.a1_r1.directlink.AllocatePrivateVirtualInterface(
                connectionId=self.conn_id, newPrivateVirtualInterfaceAllocation=newPrivateVirtualInterfaceAllocation,
                ownerAccount=self.a1_r1.config.account.account_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "DirectConnectClientException", "Connection is not available")
        finally:
            if ret:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=ret.response.virtualInterfaceId)

    @pytest.mark.region_admin
    @pytest.mark.region_directlink
    def test_T4652_valid_connection_state(self):
        ret = None
        newPrivateVirtualInterfaceAllocation = {'asn': 11111, 'virtualInterfaceName': 'test', 'vlan': 2}
        try:
            self.a1_r1.intel.dl.connection.activate(owner=self.a1_r1.config.account.account_id, connection_id=self.conn_id)
            ret = self.a1_r1.directlink.AllocatePrivateVirtualInterface(
                connectionId=self.conn_id, newPrivateVirtualInterfaceAllocation=newPrivateVirtualInterfaceAllocation,
                ownerAccount=self.a1_r1.config.account.account_id)
            assert ret.response.virtualInterfaceState == 'confirming'
            assert ret.response.asn == 11111
            assert ret.response.vlan == 2
            assert ret.response.ownerAccount == self.a1_r1.config.account.account_id
            assert ret.response.location == 'Par3'
            assert ret.response.virtualInterfaceType == 'private'
            assert ret.response.virtualInterfaceId.startswith('dxvif-')
            assert ret.response.virtualInterfaceName == 'test'
        finally:
            if ret:
                self.a1_r1.directlink.DeleteVirtualInterface(virtualInterfaceId=ret.response.virtualInterfaceId)
