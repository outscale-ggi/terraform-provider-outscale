# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.info_keys import PEERING
from qa_tina_tools.tools.tina.create_tools import create_peering
from qa_tina_tools.tools.tina.delete_tools import delete_peering


class Test_DeleteNetPeering(OscTestSuite):

    def test_T2407_dry_run(self):
        peering_info = create_peering(self.a1_r1)
        ret = self.a1_r1.oapi.DeleteNetPeering(NetPeeringId=peering_info[PEERING].id, DryRun=True)
        assert_dry_run(ret)
        delete_peering(self.a1_r1, peering_info)

    def test_T1985_no_id(self):
        try:
            self.a1_r1.oapi.DeleteNetPeering()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T1986_invalid_id(self):
        try:
            self.a1_r1.oapi.DeleteNetPeering(NetPeeringId='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T1987_unknown_ids(self):
        try:
            self.a1_r1.oapi.DeleteNetPeering(NetPeeringId='pcx-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5035')

    def test_T1988_with_peering_in_valid_state(self):
        valid_states = ['pending-acceptance', 'active', 'failed', 'deleted']
        for state in valid_states:
            peering_info = create_peering(self.a1_r1, state=state)
            assert peering_info[PEERING].status.name == state
            self.a1_r1.oapi.DeleteNetPeering(NetPeeringId=peering_info[PEERING].id)
            peering_info[PEERING].status.name = 'deleted'
            delete_peering(self.a1_r1, peering_info)

    def test_T2408_with_peering_in_invalid_state(self):
        invalid_states = ['rejected']
        for state in invalid_states:
            try:
                peering_info = create_peering(self.a1_r1, state=state)
                assert peering_info[PEERING].status.name == state
                self.a1_r1.oapi.DeleteNetPeering(NetPeeringId=peering_info[PEERING].id)
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 409, 'InvalidState', '6004')
            finally:
                delete_peering(self.a1_r1, peering_info)

    @pytest.mark.tag_sec_confidentiality
    def test_T2409_with_peering_from_another_account(self):
        peering_info = create_peering(self.a1_r1)
        try:
            self.a2_r1.oapi.DeleteNetPeering(NetPeeringId=peering_info[PEERING].id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5035')
        finally:
            delete_peering(self.a1_r1, peering_info)
