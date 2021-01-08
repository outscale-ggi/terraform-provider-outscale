# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.info_keys import PEERING
from qa_tina_tools.tools.tina.create_tools import create_peering
from qa_tina_tools.tools.tina.delete_tools import delete_peering


class Test_RejectNetPeering(OscTestSuite):

    def test_T2410_dry_run(self):
        peering_info = create_peering(self.a1_r1)
        ret = self.a1_r1.oapi.RejectNetPeering(NetPeeringId=peering_info[PEERING].id, DryRun=True)
        assert_dry_run(ret)
        delete_peering(self.a1_r1, peering_info)

    def test_T2002_no_id(self):
        try:
            self.a1_r1.oapi.RejectNetPeering()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2003_invalid_id(self):
        try:
            self.a1_r1.oapi.RejectNetPeering(NetPeeringId='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2004_unknown_ids(self):
        try:
            self.a1_r1.oapi.RejectNetPeering(NetPeeringId='pcx-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5035')

    def test_T2005_with_peering_in_valid_state(self):
        valid_states = ['pending-acceptance', 'rejected']
        for state in valid_states:
            peering_info = create_peering(self.a1_r1, state=state)
            assert peering_info[PEERING].status.name == state
            self.a1_r1.oapi.RejectNetPeering(NetPeeringId=peering_info[PEERING].id)
            peering_info[PEERING].status.name = 'rejected'
            delete_peering(self.a1_r1, peering_info)

    def test_T2411_with_peering_in_invalid_state(self):
        invalid_states = ['failed', 'deleted', 'active']
        for state in invalid_states:
            try:
                peering_info = create_peering(self.a1_r1, state=state)
                assert peering_info[PEERING].status.name == state
                self.a1_r1.oapi.RejectNetPeering(NetPeeringId=peering_info[PEERING].id)
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 409, 'InvalidState', '6004')
            finally:
                delete_peering(self.a1_r1, peering_info)

    @pytest.mark.tag_sec_confidentiality
    def test_T2412_with_peering_from_another_account(self):
        try:
            peering_info = create_peering(self.a1_r1)
            self.a2_r1.oapi.RejectNetPeering(NetPeeringId=peering_info[PEERING].id)
            peering_info[PEERING].status.name = 'rejected'
            delete_peering(self.a1_r1, peering_info)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'OperationNotSupported', '8011')

    def test_T3199_with_peering_between_two_account(self):
        self.a1_vpc = None
        self.a2_vpc = None
        self.a1_peering = None
        try:
            self.a1_vpc = self.a1_r1.oapi.CreateNet(IpRange="10.1.0.0/16").response.Net.NetId
            self.a2_vpc = self.a2_r1.oapi.CreateNet(IpRange="10.2.0.0/16").response.Net.NetId
            self.a1_peering = self.a1_r1.oapi.CreateNetPeering(
                SourceNetId=self.a1_vpc, AccepterNetId=self.a2_vpc,
            ).response.NetPeering.NetPeeringId
            self.a2_r1.oapi.RejectNetPeering(NetPeeringId=self.a1_peering)
            ret = self.a2_r1.oapi.ReadNetPeerings(Filters={'NetPeeringIds': [self.a1_peering]}).response.NetPeerings[0]
            if ret.State.Name == 'rejected':
                self.a1_peering = None
            else:
                assert False, 'Invalid expected state'
        except:
            assert False, 'No Error should occurs'
        finally:
            if self.a1_peering:
                self.a1_r1.oapi.DeleteNetPeering(NetPeeringId=self.a1_peering)
            if self.a1_vpc:
                self.a1_r1.oapi.DeleteNet(NetId=self.a1_vpc)
            if self.a2_vpc:
                self.a2_r1.oapi.DeleteNet(NetId=self.a2_vpc)
