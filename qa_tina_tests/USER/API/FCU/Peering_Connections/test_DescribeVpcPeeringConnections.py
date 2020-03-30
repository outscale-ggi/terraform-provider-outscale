# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.wait_tools import wait_vpc_peering_connections_state
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_test_tools.misc import assert_error


class Test_DescribeVpcPeeringConnections(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeVpcPeeringConnections, cls).setup_class()
        cls.a1_vpc = []
        cls.a2_vpc = []
        cls.a1_peering = []
        cls.a2_peering = []
        try:
            for i in range(2):
                cls.a1_vpc.append(create_vpc(cls.a1_r1, cidr_prefix="10.1{}".format(i), igw=False, default_rtb=True, no_ping=True))
                cls.a2_vpc.append(create_vpc(cls.a2_r1, cidr_prefix="10.2{}".format(i), igw=False, default_rtb=True, no_ping=True))
            # a1_vpc1 a1_vpc2
            # a2_vpc1 a2_vpc2
            # a1_vpc2 a2_vpc1
            # a2_vpc2 a1_vpc1
            ret = cls.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=cls.a1_vpc[0][VPC_ID], PeerOwnerId=cls.a1_r1.config.account.account_id,
                                                           PeerVpcId=cls.a1_vpc[1][VPC_ID])
            cls.a1_peering.append(ret.response.vpcPeeringConnection.vpcPeeringConnectionId)
            ret = cls.a2_r1.fcu.CreateVpcPeeringConnection(VpcId=cls.a2_vpc[0][VPC_ID], PeerOwnerId=cls.a2_r1.config.account.account_id,
                                                           PeerVpcId=cls.a2_vpc[1][VPC_ID])
            cls.a2_peering.append(ret.response.vpcPeeringConnection.vpcPeeringConnectionId)
            ret = cls.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=cls.a1_vpc[1][VPC_ID], PeerOwnerId=cls.a2_r1.config.account.account_id,
                                                           PeerVpcId=cls.a2_vpc[0][VPC_ID])
            cls.a1_peering.append(ret.response.vpcPeeringConnection.vpcPeeringConnectionId)
            ret = cls.a2_r1.fcu.CreateVpcPeeringConnection(VpcId=cls.a2_vpc[1][VPC_ID], PeerOwnerId=cls.a1_r1.config.account.account_id,
                                                           PeerVpcId=cls.a1_vpc[0][VPC_ID])
            cls.a2_peering.append(ret.response.vpcPeeringConnection.vpcPeeringConnectionId)
            cls.a1_r1.fcu.CreateTags(ResourceId=[cls.a1_peering[0]], Tag=[{'Key': 'foo', 'Value': 'bar'}])
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            for peering in cls.a1_peering:
                cls.a1_r1.fcu.DeleteVpcPeeringConnection(VpcPeeringConnectionId=peering)
            for peering in cls.a2_peering:
                cls.a2_r1.fcu.DeleteVpcPeeringConnection(VpcPeeringConnectionId=peering)
            wait_vpc_peering_connections_state(cls.a1_r1, vpc_peering_connection_id_list=cls.a1_peering, state='deleted')
            wait_vpc_peering_connections_state(cls.a2_r1, vpc_peering_connection_id_list=cls.a2_peering, state='deleted')
            for vpc_info in cls.a1_vpc:
                delete_vpc(cls.a1_r1, vpc_info)
            for vpc_info in cls.a2_vpc:
                delete_vpc(cls.a2_r1, vpc_info)
        finally:
            super(Test_DescribeVpcPeeringConnections, cls).teardown_class()

    def test_T2151_without_param(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections()
        assert len(ret.response.vpcPeeringConnectionSet) == 3
        # TODO: check response

    def test_T2475_with_invalid_peering_id(self):
        try:
            self.a1_r1.fcu.DescribeVpcPeeringConnections(VpcPeeringConnectionId='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.error_code == "VpcPeeringConnectionID.NotFound":
                known_error('TINA-4643', "Invalid error code")
            assert False, 'TODO: Remove known error'
            assert_error(error, 400, "VpcPeeringConnectionId.Malformed", "The VpcPeeringConnectionId 'foo' does not exist")

    def test_T2476_with_unknown_peering_id(self):
        try:
            self.a1_r1.fcu.DescribeVpcPeeringConnections(VpcPeeringConnectionId='pcx-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.error_code == "VpcPeeringConnectionID.NotFound":
                known_error('TINA-4643', "Invalid error code")
            assert False, 'TODO: Remove known error'
            assert_error(error, 400, "VpcPeeringConnectionId.NotFound", "The VpcPeeringConnectionId 'pcx-12345678' does not exist")

    def test_T2477_with_peering_from_another_account(self):
        try:
            self.a1_r1.fcu.DescribeVpcPeeringConnections(VpcPeeringConnectionId=self.a2_peering[0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.error_code == "VpcPeeringConnectionID.NotFound":
                known_error('TINA-4643', "Invalid error code")
            assert False, 'TODO: Remove known error'
            assert_error(error, 400, "VpcPeeringConnectionId.NotFound", "The VpcPeeringConnectionId '{}' does not exist".format(self.a2_peering[0]))

    def test_T2478_with_valid_peering_id(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(VpcPeeringConnectionId=self.a1_peering[0])
        assert len(ret.response.vpcPeeringConnectionSet) == 1

    def test_T2479_with_valid_filter_accepter_vpc_info_cidr_block(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'accepter-vpc-info.cidr-block', 'Value': ['10.20.0.0/16']}])
        assert len(ret.response.vpcPeeringConnectionSet) == 1

    def test_T2480_with_valid_filter_accepter_vpc_info_owner_id(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'accepter-vpc-info.owner-id',
                                                                    'Value': [self.a2_r1.config.account.account_id]}])
        assert len(ret.response.vpcPeeringConnectionSet) == 1

    def test_T2481_with_valid_filter_accepter_vpc_info_vpc_id(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'accepter-vpc-info.vpc-id', 'Value': [self.a2_vpc[0][VPC_ID]]}])
        assert len(ret.response.vpcPeeringConnectionSet) == 1

    def test_T2483_with_valid_filter_requester_vpc_info_cidr_block(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'requester-vpc-info.cidr-block', 'Value': ['10.10.0.0/16']}])
        assert len(ret.response.vpcPeeringConnectionSet) == 1

    def test_T2484_with_valid_filter_requester_vpc_info_owner_id(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'requester-vpc-info.owner-id',
                                                                    'Value': [self.a2_r1.config.account.account_id]}])
        assert len(ret.response.vpcPeeringConnectionSet) == 1

    def test_T2485_with_valid_filter_requester_vpc_info_vpc_id(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'requester-vpc-info.vpc-id', 'Value': [self.a1_vpc[0][VPC_ID]]}])
        assert len(ret.response.vpcPeeringConnectionSet) == 1

    def test_T2152_with_valid_filter_status_code(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'status-code', 'Value': ['pending-acceptance']}])
        assert len(ret.response.vpcPeeringConnectionSet) == 3

    def test_T2486_with_valid_filter_status_message(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'status-message',
                                                                    'Value': ["Pending accceptance by {}".format(
                                                                        self.a2_r1.config.account.account_id)]}])
        assert len(ret.response.vpcPeeringConnectionSet) == 1

    def test_T1517_with_valid_filter_vpc_peering_connection_id(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'vpc-peering-connection-id', 'Value': [self.a1_peering[0]]}])
        assert len(ret.response.vpcPeeringConnectionSet) == 1

    def test_T2487_with_valid_filter_tag(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'tag:foo', 'Value': ['bar']}])
        assert len(ret.response.vpcPeeringConnectionSet) == 1

    def test_T2488_with_valid_filter_tag_key(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'tag-key', 'Value': ['foo']}])
        assert len(ret.response.vpcPeeringConnectionSet) == 1

    def test_T2489_with_valid_filter_tag_value(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'tag-value', 'Value': ['bar']}])
        assert len(ret.response.vpcPeeringConnectionSet) == 1

    def test_T2490_with_invalid_filter_accepter_vpc_info_cidr_block(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'accepter-vpc-info.cidr-block', 'Value': ['1.2.0.0/16']}])
        assert not ret.response.vpcPeeringConnectionSet

    def test_T2491_with_invalid_filter_accepter_vpc_info_owner_id(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'accepter-vpc-info.owner-id', 'Value': ['012345678901']}])
        assert not ret.response.vpcPeeringConnectionSet

    def test_T2492_with_invalid_filter_accepter_vpc_info_vpc_id(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'accepter-vpc-info.vpc-id', 'Value': ['vpc-12345678']}])
        assert not ret.response.vpcPeeringConnectionSet

    def test_T2493_with_invalid_filter_expiration_time(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'expiration-time', 'Value': ['foo']}])
        assert not ret.response.vpcPeeringConnectionSet

    def test_T2494_with_invalid_filter_requester_vpc_info_cidr_block(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'requester-vpc-info.cidr-block', 'Value': ['1.1.0.0/16']}])
        assert not ret.response.vpcPeeringConnectionSet

    def test_T2495_with_invalid_filter_requester_vpc_info_owner_id(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'requester-vpc-info.owner-id', 'Value': ['012345678901']}])
        assert not ret.response.vpcPeeringConnectionSet

    def test_T2496_with_invalid_filter_requester_vpc_info_vpc_id(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'requester-vpc-info.vpc-id', 'Value': ['vpc-12345678']}])
        assert not ret.response.vpcPeeringConnectionSet

    def test_T2497_with_invalid_filter_status_code(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'status-code', 'Value': ['active']}])
        assert not ret.response.vpcPeeringConnectionSet

    def test_T2498_with_invalid_filter_status_message(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'status-message', 'Value': ["Active"]}])
        assert not ret.response.vpcPeeringConnectionSet

    def test_T2499_with_invalid_filter_vpc_peering_connection_id(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'vpc-peering-connection-id', 'Value': ['pcx-1234578']}])
        assert not ret.response.vpcPeeringConnectionSet

    def test_T2500_with_invalid_filter_tag(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'tag:bar', 'Value': ['foo']}])
        assert not ret.response.vpcPeeringConnectionSet

    def test_T2501_with_invalid_filter_tag_key(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'tag-key', 'Value': ['bar']}])
        assert not ret.response.vpcPeeringConnectionSet

    def test_T2502_with_invalid_filter_tag_value(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'tag-value', 'Value': ['foo']}])
        assert not ret.response.vpcPeeringConnectionSet

    def test_T2503_with_invalid_filter(self):
        try:
            self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name': 'foo', 'Value': ['bar']}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidFilter", "The filter 'foo' is invalid")

    def test_T3098_with_invalid_filter_empty_value_param(self):
        ret = self.a1_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name':'accepter-vpc-info.vpc-id', 'Value': ['']}])
        assert not ret.response.vpcPeeringConnectionSet
        ret = self.a2_r1.fcu.DescribeVpcPeeringConnections(Filter=[{'Name':'requester-vpc-info.owner-id', 'Value': ['']}])
        assert not  ret.response.vpcPeeringConnectionSet
