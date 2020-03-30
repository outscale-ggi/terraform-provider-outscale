# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import re

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.wait_tools import wait_vpc_peering_connections_state
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_test_tools.misc import assert_error


class Test_CreateVpcPeeringConnection(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateVpcPeeringConnection, cls).setup_class()
        cls.vpc_info_1 = None
        cls.vpc_info_2 = None
        cls.peering = None

    def setup_method(self, method):
        super(Test_CreateVpcPeeringConnection, self).setup_method(method)
        self.vpc_info_1 = None
        self.vpc_info_2 = None
        self.peering = None
        try:
            self.vpc_info_1 = create_vpc(self.a1_r1, cidr_prefix="10.1", igw=False, default_rtb=True, no_ping=True)
            self.vpc_info_2 = create_vpc(self.a1_r1, cidr_prefix="10.2", igw=False, default_rtb=True, no_ping=True)
        except:
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.peering:
                self.a1_r1.fcu.DeleteVpcPeeringConnection(VpcPeeringConnectionId=self.peering)
                wait_vpc_peering_connections_state(self.a1_r1, vpc_peering_connection_id_list=[self.peering], state='deleted')
            if self.vpc_info_2:
                delete_vpc(self.a1_r1, self.vpc_info_2)
            if self.vpc_info_1:
                delete_vpc(self.a1_r1, self.vpc_info_1)
        finally:
            super(Test_CreateVpcPeeringConnection, self).teardown_method(method)

    def test_T2458_with_valid_param(self):
        ret = self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=self.vpc_info_1[VPC_ID], PeerVpcId=self.vpc_info_2[VPC_ID])
        self.peering = ret.response.vpcPeeringConnection.vpcPeeringConnectionId
        assert ret.response.vpcPeeringConnection.accepterVpcInfo.cidrBlock == "10.2.0.0/16"
        assert ret.response.vpcPeeringConnection.accepterVpcInfo.ownerId == self.a1_r1.config.account.account_id
        assert ret.response.vpcPeeringConnection.accepterVpcInfo.vpcId == self.vpc_info_2[VPC_ID]
        # assert ret.response.vpcPeeringConnection.expirationTime
        assert ret.response.vpcPeeringConnection.requesterVpcInfo.cidrBlock == "10.1.0.0/16"
        assert ret.response.vpcPeeringConnection.requesterVpcInfo.ownerId == self.a1_r1.config.account.account_id
        assert ret.response.vpcPeeringConnection.requesterVpcInfo.vpcId == self.vpc_info_1[VPC_ID]
        assert ret.response.vpcPeeringConnection.status.code == "pending-acceptance"
        assert ret.response.vpcPeeringConnection.status.message == "Pending accceptance by {}".format(self.a1_r1.config.account.account_id)
        assert not ret.response.vpcPeeringConnection.tagSet
        assert re.search(r"(pcx-[a-zA-Z0-9]{8})", ret.response.vpcPeeringConnection.vpcPeeringConnectionId)

    def test_T2459_without_vpc_id(self):
        try:
            self.a1_r1.fcu.CreateVpcPeeringConnection(PeerVpcId=self.vpc_info_2[VPC_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message == "The request must contain the parameter: vpcId":
                known_error("TINA-4643", "Invalid error message")
            assert False, "Remove known error"
            assert_error(error, 400, "MissingParameter", "The request must contain the parameter: VpcId")

    def test_T2460_without_peer_vpc_id(self):
        try:
            self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=self.vpc_info_1[VPC_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message == "The request must contain the parameter: vpcId":
                known_error("TINA-4643", "Invalid error message")
            assert False, "Remove known error"
            assert_error(error, 400, "MissingParameter", "The request must contain the parameter: PeerVpcId")

    def test_T2461_with_peer_owner_id(self):
        ret = self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=self.vpc_info_1[VPC_ID], PeerVpcId=self.vpc_info_2[VPC_ID],
                                                        PeerOwnerId=self.a1_r1.config.account.account_id)
        self.peering = ret.response.vpcPeeringConnection.vpcPeeringConnectionId

    def test_T2462_with_invalid_vpc_id(self):
        try:
            self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId='foo', PeerVpcId=self.vpc_info_2[VPC_ID],
                                                      PeerOwnerId=self.a2_r1.config.account.account_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidVpcId.Malformed", "Invalid id 'foo' (must be 'vpc-...')")

    def test_T2463_with_unknown_vpc_id(self):
        try:
            self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId='vpc-12345678', PeerVpcId=self.vpc_info_2[VPC_ID],
                                                      PeerOwnerId=self.a2_r1.config.account.account_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.error_code == "InvalidVpcID.NotFound":
                known_error('TINA-4643', "Invalid error code")
            assert False, 'TODO: Remove known error'
            assert_error(error, 400, "InvalidVpcId.NotFound", "The VpcId 'vpc-12345678' does not exist")

    def test_T2464_with_vpc_id_from_another_account(self):
        vpc_info_3 = create_vpc(self.a2_r1, cidr_prefix="10.3", igw=False, default_rtb=True, no_ping=True)
        try:
            self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=vpc_info_3[VPC_ID], PeerVpcId=self.vpc_info_2[VPC_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.error_code == "InvalidVpcID.NotFound":
                known_error('TINA-4643', "Invalid error code")
            assert False, 'TODO: Remove known error'
            assert_error(error, 400, "InvalidVpcId.NotFound", "The vpc ID '{}' does not exist".format(vpc_info_3[VPC_ID]))
        finally:
            delete_vpc(self.a2_r1, vpc_info_3)

    def test_T2465_with_invalid_peer_vpc_id(self):
        try:
            self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=self.vpc_info_1[VPC_ID], PeerVpcId='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.error_code == "InvalidVpcId.Malformed":
                known_error('TINA-4643', "Invalid error code")
            assert False, 'TODO: Remove known error'
            assert_error(error, 400, "InvalidPeerVpcId.Malformed", "Invalid id 'foo' (must be 'vpc-...')")

    def test_T2466_with_unknown_peer_vpc_id(self):
        try:
            ret = self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=self.vpc_info_1[VPC_ID], PeerVpcId='vpc-12345678')
            self.peering = ret.response.vpcPeeringConnection.vpcPeeringConnectionId
            assert ret.response.vpcPeeringConnection.status.code == 'failed'
            assert ret.response.vpcPeeringConnection.status.message == 'Failed due to incorrect VPC-ID, Account ID, or overlapping CIDR range'
            # Jira TINA-4643...
        except OscApiException as error:
            assert_error(error, 400, "InvalidPeerVpcId.NotFound", "The vpc ID 'vpc-12345678' does not exist")

    def test_T2467_with_peer_vpc_id_from_another_account(self):
        vpc_info_3 = create_vpc(self.a2_r1, cidr_prefix="10.3", igw=False, default_rtb=True, no_ping=True)
        try:
            ret = self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=self.vpc_info_1[VPC_ID], PeerVpcId=vpc_info_3[VPC_ID])
            self.peering = ret.response.vpcPeeringConnection.vpcPeeringConnectionId
            assert ret.response.vpcPeeringConnection.status.code == 'failed'
            assert ret.response.vpcPeeringConnection.status.message == 'Failed due to incorrect VPC-ID, Account ID, or overlapping CIDR range'
            # Jira TINA-4643...
        except OscApiException as error:
            assert_error(error, 400, "InvalidPeerVpcId.NotFound", "The vpc ID '{}' does not exist".format(vpc_info_3[VPC_ID]))
        finally:
            delete_vpc(self.a2_r1, vpc_info_3)

    def test_T2468_with_same_vpc(self):
        try:
            self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=self.vpc_info_1[VPC_ID], PeerVpcId=self.vpc_info_1[VPC_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterValue",
                         "Invalid value '{}' for peerVpcId. Both vpcId and peerVpcId values must be different.".format(self.vpc_info_1[VPC_ID]))

    def test_T2469_with_same_cidr(self):
        vpc_info_3 = create_vpc(self.a1_r1, cidr_prefix="10.1", igw=False, default_rtb=True, no_ping=True)
        try:
            ret = self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=self.vpc_info_1[VPC_ID], PeerVpcId=vpc_info_3[VPC_ID])
            self.peering = ret.response.vpcPeeringConnection.vpcPeeringConnectionId
            assert ret.response.vpcPeeringConnection.status.code == 'failed'
            assert ret.response.vpcPeeringConnection.status.message == 'Failed due to incorrect VPC-ID, Account ID, or overlapping CIDR range'
        finally:
            delete_vpc(self.a1_r1, vpc_info_3)

    def test_T2470_with_valid_peer_owner(self):
        vpc_info_3 = create_vpc(self.a2_r1, cidr_prefix="10.3", igw=False, default_rtb=True, no_ping=True)
        try:
            ret = self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=self.vpc_info_1[VPC_ID], PeerVpcId=vpc_info_3[VPC_ID],
                                                            PeerOwnerId=self.a2_r1.config.account.account_id)
            self.peering = ret.response.vpcPeeringConnection.vpcPeeringConnectionId
            assert ret.response.vpcPeeringConnection.status.code == 'pending-acceptance'
        finally:
            if self.peering:
                self.a1_r1.fcu.DeleteVpcPeeringConnection(VpcPeeringConnectionId=self.peering)
                wait_vpc_peering_connections_state(self.a1_r1, vpc_peering_connection_id_list=[self.peering], state='deleted')
                self.peering = None
            delete_vpc(self.a2_r1, vpc_info_3)

    def test_T2471_with_invalid_peer_owner(self):
        try:
            ret = self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=self.vpc_info_1[VPC_ID], PeerVpcId=self.vpc_info_2[VPC_ID], PeerOwnerId='foo')
            self.peering = ret.response.vpcPeeringConnection.vpcPeeringConnectionId
            assert ret.response.vpcPeeringConnection.status.code == 'failed'
            assert ret.response.vpcPeeringConnection.status.message == 'Failed due to incorrect VPC-ID, Account ID, or overlapping CIDR range'
            # Jira TINA-4643...
        except OscApiException as error:
            assert_error(error, 400, "InvalidPeerOwnerId.NotFound", "...")

    def test_T2472_with_unknown_peer_owner(self):
        try:
            ret = self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=self.vpc_info_1[VPC_ID], PeerVpcId=self.vpc_info_2[VPC_ID],
                                                            PeerOwnerId='012345678901')
            self.peering = ret.response.vpcPeeringConnection.vpcPeeringConnectionId
            assert ret.response.vpcPeeringConnection.status.code == 'failed'
            assert ret.response.vpcPeeringConnection.status.message == 'Failed due to incorrect VPC-ID, Account ID, or overlapping CIDR range'
            # Jira TINA-4643...
        except OscApiException as error:
            assert_error(error, 400, "InvalidPeerOwnerId.NotFound", "...")

    def test_T2473_with_wrong_peer_owner(self):
        vpc_info_3 = create_vpc(self.a2_r1, cidr_prefix="10.3", igw=False, default_rtb=True, no_ping=True)
        try:
            ret = self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=self.vpc_info_1[VPC_ID], PeerVpcId=vpc_info_3[VPC_ID],
                                                            PeerOwnerId=self.a1_r1.config.account.account_id)
            self.peering = ret.response.vpcPeeringConnection.vpcPeeringConnectionId
            assert ret.response.vpcPeeringConnection.status.code == 'failed'
            assert ret.response.vpcPeeringConnection.status.message == 'Failed due to incorrect VPC-ID, Account ID, or overlapping CIDR range'
            # Jira TINA-4643...
        except OscApiException as error:
            assert_error(error, 400, "InvalidPeerOwnerId.NotFound", "...")
        finally:
            delete_vpc(self.a2_r1, vpc_info_3)

    def test_T2474_duplicated_peering(self):
        ret = self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=self.vpc_info_1[VPC_ID], PeerVpcId=self.vpc_info_2[VPC_ID])
        self.peering = ret.response.vpcPeeringConnection.vpcPeeringConnectionId
        self.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=self.vpc_info_1[VPC_ID], PeerVpcId=self.vpc_info_2[VPC_ID])
        assert self.peering == ret.response.vpcPeeringConnection.vpcPeeringConnectionId
