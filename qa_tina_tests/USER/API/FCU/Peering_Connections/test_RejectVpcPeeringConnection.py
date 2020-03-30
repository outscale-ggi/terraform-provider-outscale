# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_test_tools.misc import assert_error
from qa_tina_tools.tools.tina.create_tools import create_peering
from qa_tina_tools.tools.tina.create_tools import delete_peering
from qa_tina_tools.tina.info_keys import PEERING


class Test_RejectVpcPeeringConnection(OscTestSuite):

    def test_T2452_no_id(self):
        try:
            self.a1_r1.fcu.RejectVpcPeeringConnection()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message == "The request must contain the parameter: vpcPeeringConnectionId":
                known_error('TINA-4643', "Invalid error message")
            assert False, 'TODO: Remove known error'
            assert_error(error, 400, "MissingParameter", "The request must contain the parameter: VpcPeeringConnectionId")

    def test_T2453_invalid_id(self):
        try:
            self.a1_r1.fcu.RejectVpcPeeringConnection(VpcPeeringConnectionId='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidVpcPeeringConnectionId.Malformed", "Invalid id 'foo' (must be 'pcx-...')")

    def test_T2454_unknown_id(self):
        try:
            self.a1_r1.fcu.RejectVpcPeeringConnection(VpcPeeringConnectionId='pcx-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.error_code == "InvalidVpcPeeringConnectionID.NotFound":
                known_error('TINA-4643', "Invalid error code")
            assert False, 'TODO: Remove known error'
            assert_error(error, 400, "InvalidVpcPeeringConnectionId.NotFound", "The VpcPeeringConnectionId 'pcx-12345678' does not exist")

    def test_T2455_with_peering_in_valid_state(self):
        valid_states = ['pending-acceptance', 'rejected']
        for state in valid_states:
            peering_info = create_peering(self.a1_r1, state=state)
            assert peering_info[PEERING].status.name == state
            ret = self.a1_r1.fcu.RejectVpcPeeringConnection(VpcPeeringConnectionId=peering_info[PEERING].id)
            assert ret.response.osc_return == 'true'
            peering_info[PEERING].status.name = 'rejected'
            delete_peering(self.a1_r1, peering_info)

    def test_T2456_with_peering_in_invalid_state(self):
        invalid_states = ['failed', 'deleted', 'active']
        for state in invalid_states:
            try:
                peering_info = create_peering(self.a1_r1, state=state)
                assert peering_info[PEERING].status.name == state
                self.a1_r1.fcu.RejectVpcPeeringConnection(VpcPeeringConnectionId=peering_info[PEERING].id)
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error,
                             400,
                             "InvalidStateTransition",
                             "Invalid state transition for peering connection '{}'. Transition from state '{}' to 'rejected' is not possible".format(
                                 peering_info[PEERING].id, state))
            finally:
                delete_peering(self.a1_r1, peering_info)

    def test_T2457_with_peering_from_another_account(self):
        peering_info = create_peering(self.a1_r1)
        try:
            self.a2_r1.fcu.RejectVpcPeeringConnection(VpcPeeringConnectionId=peering_info[PEERING].id)
            peering_info[PEERING].status.name = 'rejected'
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "OperationNotPermitted",
                         "User '{}' cannot reject vpc peering connection '{}'".format(self.a2_r1.config.account.account_id,
                peering_info[PEERING].id))
        finally:
            delete_peering(self.a1_r1, peering_info)
