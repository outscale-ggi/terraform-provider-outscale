# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_test_tools.misc import assert_error
from qa_tina_tools.tools.tina.create_tools import create_peering
from qa_tina_tools.tools.tina.create_tools import delete_peering
from qa_tina_tools.tina.info_keys import PEERING


class Test_DeleteVpcPeeringConnection(OscTestSuite):

    def test_T2446_no_id(self):
        try:
            self.a1_r1.fcu.DeleteVpcPeeringConnection()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message == "The request must contain the parameter: vpcPeeringConnectionId":
                known_error('TINA-4643', "Invalid error message")
            assert False, 'TODO: Remove known error'
            assert_error(error, 400, "MissingParameter", "The request must contain the parameter: VpcPeeringConnectionId")

    def test_T2447_invalid_id(self):
        try:
            self.a1_r1.fcu.DeleteVpcPeeringConnection(VpcPeeringConnectionId='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidVpcPeeringConnectionId.Malformed", "Invalid id 'foo' (must be 'pcx-...')")

    def test_T2448_unknown_id(self):
        try:
            self.a1_r1.fcu.DeleteVpcPeeringConnection(VpcPeeringConnectionId='pcx-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.error_code == "InvalidVpcPeeringConnectionID.NotFound":
                known_error('TINA-4643', "Invalid error code")
            assert False, 'TODO: Remove known error'
            assert_error(error, 400, "InvalidVpcPeeringConnectionId.NotFound", "The VpcPeeringConnectionId 'pcx-12345678' does not exist")

    def test_T2449_with_peering_in_valid_state(self):
        valid_states = ['pending-acceptance', 'active', 'failed', 'deleted']
        for state in valid_states:
            peering_info = create_peering(self.a1_r1, state=state)
            assert peering_info[PEERING].status.name == state
            ret = self.a1_r1.fcu.DeleteVpcPeeringConnection(VpcPeeringConnectionId=peering_info[PEERING].id)
            assert ret.response.osc_return == 'true'
            peering_info[PEERING].status.name = 'deleted'
            delete_peering(self.a1_r1, peering_info)

    def test_T2450_with_peering_in_invalid_state(self):
        invalid_states = ['rejected']
        for state in invalid_states:
            try:
                peering_info = create_peering(self.a1_r1, state=state)
                assert peering_info[PEERING].status.name == state
                self.a1_r1.fcu.DeleteVpcPeeringConnection(VpcPeeringConnectionId=peering_info[PEERING].id)
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error,
                             400,
                             "InvalidStateTransition",
                             "Invalid state transition for peering connection '{}'. Transition from state '{}' to 'deleted' is not possible".format(
                                 peering_info[PEERING].id, state))
            finally:
                delete_peering(self.a1_r1, peering_info)

    def test_T2451_with_peering_from_another_account(self):
        peering_info = create_peering(self.a1_r1)
        try:
            self.a2_r1.fcu.DeleteVpcPeeringConnection(VpcPeeringConnectionId=peering_info[PEERING].id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.error_code == "InvalidVpcPeeringConnectionID.NotFound":
                known_error('TINA-4643', "Invalid error code")
            assert False, 'TODO: Remove known error'
            assert_error(error, 400, "InvalidVpcPeeringConnectionId.NotFound", "The VpcPeeringConnectionId '{}' does not exist".format(
                peering_info[PEERING].id))
        finally:
            delete_peering(self.a1_r1, peering_info)
