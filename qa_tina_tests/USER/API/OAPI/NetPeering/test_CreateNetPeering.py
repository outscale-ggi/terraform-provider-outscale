# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import re

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_tina_tools.tools.tina.wait_tools import wait_vpc_peering_connections_state


class Test_CreateNetPeering(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateNetPeering, cls).setup_class()
        cls.vpc_info_1 = None
        cls.vpc_info_2 = None
        cls.peering = None

    def setup_method(self, method):
        super(Test_CreateNetPeering, self).setup_method(method)
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
                self.a1_r1.oapi.DeleteNetPeering(NetPeeringId=self.peering)
                wait_vpc_peering_connections_state(self.a1_r1, vpc_peering_connection_id_list=[self.peering], state='deleted')
            if self.vpc_info_2:
                delete_vpc(self.a1_r1, self.vpc_info_2)
            if self.vpc_info_1:
                delete_vpc(self.a1_r1, self.vpc_info_1)
        finally:
            super(Test_CreateNetPeering, self).teardown_method(method)

    def test_T2413_dry_run(self):
        ret = self.a1_r1.oapi.CreateNetPeering(SourceNetId=self.vpc_info_1[VPC_ID], AccepterNetId=self.vpc_info_2[VPC_ID], DryRun=True)
        assert_dry_run(ret)

    def test_T1983_with_valid_param(self):
        ret = self.a1_r1.oapi.CreateNetPeering(SourceNetId=self.vpc_info_1[VPC_ID], AccepterNetId=self.vpc_info_2[VPC_ID])
        self.peering = ret.response.NetPeering.NetPeeringId
        assert ret.response.NetPeering.AccepterNet.IpRange == "10.2.0.0/16"
        assert ret.response.NetPeering.AccepterNet.AccountId == self.a1_r1.config.account.account_id
        assert ret.response.NetPeering.AccepterNet.NetId == self.vpc_info_2[VPC_ID]
        assert ret.response.NetPeering.SourceNet.IpRange == "10.1.0.0/16"
        assert ret.response.NetPeering.SourceNet.AccountId == self.a1_r1.config.account.account_id
        assert ret.response.NetPeering.SourceNet.NetId == self.vpc_info_1[VPC_ID]
        assert ret.response.NetPeering.State.Name == "pending-acceptance"
        assert ret.response.NetPeering.State.Message == "Pending accceptance by {}".format(self.a1_r1.config.account.account_id)
        assert not ret.response.NetPeering.Tags
        assert re.search(r"(pcx-[a-zA-Z0-9]{8})", ret.response.NetPeering.NetPeeringId)

    def test_T2414_without_source_net_id(self):
        try:
            self.a1_r1.oapi.CreateNetPeering(AccepterNetId=self.vpc_info_2[VPC_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2415_without_accepter_net_id(self):
        try:
            self.a1_r1.oapi.CreateNetPeering(SourceNetId=self.vpc_info_1[VPC_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2416_with_invalid_source_net_id(self):
        try:
            self.a1_r1.oapi.CreateNetPeering(SourceNetId='foo', AccepterNetId=self.vpc_info_2[VPC_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2417_with_unknown_source_net_id(self):
        try:
            self.a1_r1.oapi.CreateNetPeering(SourceNetId='vpc-12345678', AccepterNetId=self.vpc_info_2[VPC_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5065')

    @pytest.mark.tag_sec_confidentiality
    def test_T2418_with_source_net_id_from_another_account(self):
        vpc_info_3 = create_vpc(self.a2_r1, cidr_prefix="10.3", igw=False, default_rtb=True, no_ping=True)
        try:
            self.a1_r1.oapi.CreateNetPeering(SourceNetId=vpc_info_3[VPC_ID], AccepterNetId=self.vpc_info_2[VPC_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5065')
        finally:
            delete_vpc(self.a2_r1, vpc_info_3)

    def test_T2419_with_invalid_accepter_net_id(self):
        try:
            self.a1_r1.oapi.CreateNetPeering(SourceNetId=self.vpc_info_1[VPC_ID], AccepterNetId='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5065')

    def test_T2420_with_unknown_accepter_net_id(self):
        try:
            ret = self.a1_r1.oapi.CreateNetPeering(SourceNetId=self.vpc_info_1[VPC_ID], AccepterNetId='vpc-12345678')
            self.peering = ret.response.NetPeering.NetPeeringId
            assert ret.response.NetPeering.State.Name == 'failed'
            assert ret.response.NetPeering.State.Message == 'Failed due to incorrect VPC-ID, Account ID, or overlapping CIDR range'
            # Jira TINA-4643...
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5065')

    @pytest.mark.tag_sec_confidentiality
    def test_T2421_with_accepter_net_id_from_another_account(self):
        vpc_info_3 = create_vpc(self.a2_r1, cidr_prefix="10.3", igw=False, default_rtb=True, no_ping=True)
        try:
            ret = self.a1_r1.oapi.CreateNetPeering(SourceNetId=self.vpc_info_1[VPC_ID], AccepterNetId=vpc_info_3[VPC_ID])
            self.peering = ret.response.NetPeering.NetPeeringId
            assert ret.response.NetPeering.State.Name == "pending-acceptance"
            assert ret.response.NetPeering.State.Message == "Pending accceptance by {}".format(
                self.a2_r1.config.account.account_id)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5065')
        finally:
            delete_vpc(self.a2_r1, vpc_info_3)
            self.peering = None

    def test_T1981_with_same_net(self):
        try:
            self.a1_r1.oapi.CreateNetPeering(SourceNetId=self.vpc_info_1[VPC_ID], AccepterNetId=self.vpc_info_1[VPC_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T2422_with_same_ip_range(self):
        vpc_info_3 = create_vpc(self.a1_r1, cidr_prefix="10.1", igw=False, default_rtb=True, no_ping=True)
        try:
            ret = self.a1_r1.oapi.CreateNetPeering(SourceNetId=self.vpc_info_1[VPC_ID], AccepterNetId=vpc_info_3[VPC_ID])
            self.peering = ret.response.NetPeering.NetPeeringId
            assert ret.response.NetPeering.State.Name == 'failed'
            assert ret.response.NetPeering.State.Message == 'Failed due to incorrect VPC-ID, Account ID, or overlapping CIDR range'
        finally:
            delete_vpc(self.a1_r1, vpc_info_3)

    def test_T2423_duplicated_peering(self):
        ret = self.a1_r1.oapi.CreateNetPeering(SourceNetId=self.vpc_info_1[VPC_ID], AccepterNetId=self.vpc_info_2[VPC_ID])
        self.peering = ret.response.NetPeering.NetPeeringId
        ret = self.a1_r1.oapi.CreateNetPeering(SourceNetId=self.vpc_info_1[VPC_ID], AccepterNetId=self.vpc_info_2[VPC_ID])
        assert self.peering == ret.response.NetPeering.NetPeeringId
