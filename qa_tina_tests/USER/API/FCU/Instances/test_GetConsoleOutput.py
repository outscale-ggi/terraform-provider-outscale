import pytest

from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances, terminate_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_common_tools.misc import assert_error
import datetime
import re
import time
import base64
import binascii
TIMESTAMP_REGEX = r'(^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z$)'


class Test_GetConsoleOutput(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_GetConsoleOutput, cls).setup_class()
        cls.instance_info_a1 = None
        cls.instance_info_a2 = None
        try:
            cls.instance_info_a1 = create_instances(cls.a1_r1, state=None, nb=3)
            cls.instance_info_a2 = create_instances(cls.a2_r1, state=None)
            wait_instances_state(cls.a1_r1, cls.instance_info_a1[INSTANCE_ID_LIST], state='running')
            wait_instances_state(cls.a2_r1, cls.instance_info_a2[INSTANCE_ID_LIST], state='running')
        except Exception as error:
            try:
                cls.teardown_class()
            except:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.instance_info_a1:
                delete_instances(cls.a1_r1, cls.instance_info_a1)
            if cls.instance_info_a2:
                delete_instances(cls.a2_r1, cls.instance_info_a2)
        finally:
            super(Test_GetConsoleOutput, cls).teardown_class()

    def check_response(self, ret, inst_id):
        assert ret.response.output
        try:
            base64.b64decode(ret.response.output)
        except binascii.Error:
            assert False, "Response output is not base64"
        assert ret.response.instanceId == inst_id
        assert ret.response.timestamp and re.match(TIMESTAMP_REGEX, ret.response.timestamp)

    def test_T4360_with_valid_params(self):
        inst_id = self.instance_info_a1[INSTANCE_ID_LIST][0]
        start = datetime.datetime.now()

        while datetime.datetime.now() - start < datetime.timedelta(seconds=30):
            ret = self.a1_r1.fcu.GetConsoleOutput(InstanceId=inst_id)
            if ret.response.output:
                break
            time.sleep(3)
        self.check_response(ret, inst_id)

    def test_T4359_with_incorrect_id(self):
        try:
            self.a1_r1.fcu.GetConsoleOutput(InstanceId='i-88888888')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound', 'The instance IDs do not exist: i-88888888')

    @pytest.mark.tag_sec_confidentiality
    def test_T4358_with_id_of_other_account(self):
        try:
            self.a1_r1.fcu.GetConsoleOutput(InstanceId=self.instance_info_a2[INSTANCE_ID_LIST][0])
            assert False, 'Remove known error code'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound', 'The instance IDs do not exist: {}'.
                         format(self.instance_info_a2[INSTANCE_ID_LIST][0]))

    def test_T4357_with_invalid_id(self):
        try:
            self.a1_r1.fcu.GetConsoleOutput(InstanceId='toto')
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.Malformed', 'Invalid ID received: toto. Expected format: i-')

    def test_T4356_with_terminated_instance(self):
        inst_id = self.instance_info_a1[INSTANCE_ID_LIST][1]
        terminate_instances(self.a1_r1, [inst_id])
        ret = self.a1_r1.fcu.GetConsoleOutput(InstanceId=inst_id)
        self.check_response(ret, inst_id)

    def test_T4355_with_stopped_instance(self):
        inst_id = self.instance_info_a1[INSTANCE_ID_LIST][2]
        stop_instances(self.a1_r1, [inst_id])
        ret = self.a1_r1.fcu.GetConsoleOutput(InstanceId=inst_id)
        self.check_response(ret, inst_id)
