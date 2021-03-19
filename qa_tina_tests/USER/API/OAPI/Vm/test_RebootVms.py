
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


class Test_RebootVms(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_RebootVms, cls).setup_class()
        cls.info = None
        try:
            cls.info = create_instances(cls.a1_r1, nb=10, state='running')
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            # ret = cls.a1_r1.oapi.ReadVms(Filters={'VmIds': cls.info[INSTANCE_ID_LIST]}).response.Vms
            # cls.info[INSTANCE_ID_LIST] = [inst.VmId for inst in ret]
            delete_instances(cls.a1_r1, cls.info)
        finally:
            super(Test_RebootVms, cls).teardown_class()

    def test_T2086_without_ids(self):
        try:
            self.a1_r1.oapi.RebootVms()
            assert False, 'Call without ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2087_with_empty_ids(self):
        try:
            self.a1_r1.oapi.RebootVms(VmIds=[])
            assert False, 'Call without ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2088_with_invalid_ids(self):
        try:
            self.a1_r1.oapi.RebootVms(VmIds=['foo'])
            assert False, 'Call with invalid ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2089_from_running(self):
        self.a1_r1.oapi.RebootVms(VmIds=[self.info[INSTANCE_ID_LIST][0]])
        wait_instances_state(self.a1_r1, [self.info[INSTANCE_ID_LIST][0]], state='running')

    def test_T2090_from_ready(self):
        wait_instances_state(self.a1_r1, [self.info[INSTANCE_ID_LIST][1]], state='ready')
        self.a1_r1.oapi.RebootVms(VmIds=[self.info[INSTANCE_ID_LIST][1]])
        wait_instances_state(self.a1_r1, [self.info[INSTANCE_ID_LIST][1]], state='running')

    def test_T2091_from_stop(self):
        self.a1_r1.oapi.StopVms(VmIds=[self.info[INSTANCE_ID_LIST][2]], ForceStop=False)
        try:
            self.a1_r1.oapi.RebootVms(VmIds=[self.info[INSTANCE_ID_LIST][2]])
            assert False, 'Call with stopping instance should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'InvalidState', '6003')

    def test_T2092_from_stopped(self):
        self.a1_r1.oapi.StopVms(VmIds=[self.info[INSTANCE_ID_LIST][3]], ForceStop=False)
        wait_instances_state(self.a1_r1, [self.info[INSTANCE_ID_LIST][3]], state='stopped')
        try:
            self.a1_r1.oapi.RebootVms(VmIds=[self.info[INSTANCE_ID_LIST][3]])
            assert False, 'Call with stopped instance should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'InvalidState', '6003')

    def test_T2093_from_terminated(self):
        try:
            vm_id = self.info[INSTANCE_ID_LIST][4]
            self.a1_r1.oapi.DeleteVms(VmIds=[vm_id])
            wait_instances_state(self.a1_r1, [vm_id], state='terminated')
            self.a1_r1.oapi.RebootVms(VmIds=[vm_id])
            assert False, 'Call with terminated instance should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'InvalidState', '6003')

    def test_T2094_with_unknown_param(self):
        try:
            self.a1_r1.oapi.RebootVms(VmIds=[self.info[INSTANCE_ID_LIST][5]], foo='bar')
            assert False, 'Call with unknown parameter should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T2095_with_unknown_ids(self):
        try:
            self.a1_r1.oapi.RebootVms(VmIds=['i-12345678'])
            assert False, 'Call with invalid ids should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')

    @pytest.mark.tag_sec_confidentiality
    def test_T2096_with_instance_from_another_account(self):
        infouser2 = create_instances(self.a2_r1, state='running')
        try:
            self.a1_r1.oapi.RebootVms(VmIds=[infouser2[INSTANCE_ID_LIST][0]])
            assert False, 'Call with instance from another account should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')
        finally:
            delete_instances(self.a2_r1, infouser2)

    def test_T2097_with_multiple_valid_instances(self):
        self.a1_r1.oapi.RebootVms(VmIds=self.info[INSTANCE_ID_LIST][6:8])

    def test_T2098_with_multiple_valid_and_invalid_instances(self):
        try:
            self.a1_r1.oapi.RebootVms(VmIds=[self.info[INSTANCE_ID_LIST][9]] + ['i-12345678'])
            assert False, 'Call with invalid instance should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')
