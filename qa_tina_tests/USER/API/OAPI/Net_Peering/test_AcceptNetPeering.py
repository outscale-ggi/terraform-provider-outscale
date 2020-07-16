# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.object import Peering
from qa_tina_tools.tools.tina.create_tools import create_peering
from qa_tina_tools.tools.tina.delete_tools import delete_peering
from qa_tina_tools.tools.tina.info_keys import PEERING


class Test_AcceptNetPeering(OscTestSuite):

    def test_T2404_dry_run(self):
        peering_info = create_peering(self.a1_r1)
        ret = self.a1_r1.oapi.AcceptNetPeering(NetPeeringId=peering_info[PEERING].id, DryRun=True)
        assert_dry_run(ret)

    def test_T1976_no_id(self):
        try:
            self.a1_r1.oapi.AcceptNetPeering()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T1977_invalid_id(self):
        try:
            self.a1_r1.oapi.AcceptNetPeering(NetPeeringId='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T1978_unknown_ids(self):
        try:
            self.a1_r1.oapi.AcceptNetPeering(NetPeeringId='pcx-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5035')

    def test_T1979_with_peering_in_valid_state(self):
        valid_states = ['pending-acceptance', 'active']
        for state in valid_states:
            peering_info = create_peering(self.a1_r1, state=state)
            assert peering_info[PEERING].status.name == state
            ret = self.a1_r1.oapi.AcceptNetPeering(NetPeeringId=peering_info[PEERING].id)
            peering = Peering(net_peering=ret.response.NetPeering)
            peering_info[PEERING].status.name = 'active'
            peering_info[PEERING].status.message = 'Active'
            assert peering == peering_info[PEERING]
            delete_peering(self.a1_r1, peering_info)

    def test_T2405_with_peering_in_invalid_state(self):
        invalid_states = ['failed', 'rejected', 'deleted']
        peering_info = None
        for state in invalid_states:
            try:
                peering_info = create_peering(self.a1_r1, state=state)
                assert peering_info[PEERING].status.name == state
                self.a1_r1.oapi.AcceptNetPeering(NetPeeringId=peering_info[PEERING].id)
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 409, 'InvalidState', '6004')
            finally:
                delete_peering(self.a1_r1, peering_info)

    @pytest.mark.tag_sec_confidentiality
    def test_T2406_with_peering_from_another_account(self):
        peering_info = create_peering(self.a1_r1)
        try:
            self.a2_r1.oapi.AcceptNetPeering(NetPeeringId=peering_info[PEERING].id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5035')
        finally:
            delete_peering(self.a1_r1, peering_info)

    def test_T3198_with_peering_between_two_account(self):
        self.a1_vpc = None
        self.a2_vpc = None
        self.a1_peering = None
        try:
            self.a1_vpc = self.a1_r1.oapi.CreateNet(IpRange="10.1.0.0/16").response.Net.NetId
            self.a2_vpc = self.a2_r1.oapi.CreateNet(IpRange="10.2.0.0/16").response.Net.NetId
            self.a1_peering = self.a1_r1.oapi.CreateNetPeering(
                SourceNetId=self.a1_vpc, AccepterNetId=self.a2_vpc,
            ).response.NetPeering.NetPeeringId
            self.a2_r1.oapi.AcceptNetPeering(NetPeeringId=self.a1_peering)
            ret = self.a2_r1.oapi.ReadNetPeerings(Filters={'NetPeeringIds':[self.a1_peering]}).response.NetPeerings[0]
            assert ret.State.Name == 'active'
        except OscApiException:
            assert False, 'No Error should occurs'
        finally:
            if self.a1_peering:
                self.a1_r1.oapi.DeleteNetPeering(NetPeeringId=self.a1_peering)
            if self.a1_vpc:
                self.a1_r1.oapi.DeleteNet(NetId=self.a1_vpc)
            if self.a2_vpc:
                self.a2_r1.oapi.DeleteNet(NetId=self.a2_vpc)
