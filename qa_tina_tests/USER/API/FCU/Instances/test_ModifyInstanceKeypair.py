# pylint: disable=missing-docstring

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST


class Test_ModifyInstanceKeypair(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ModifyInstanceKeypair, cls).setup_class()
        cls.keyname = 'keyName'
        cls.inst_info = None
        try:
            cls.inst_info = create_instances(cls.a1_r1)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_ModifyInstanceKeypair, cls).teardown_class()

    def test_T4082_with_instance_id(self):
        try:
            self.a1_r1.fcu.ModifyInstanceKeypair(InstanceId=self.inst_info[INSTANCE_ID_LIST][0])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'MissingParameter', 'The request must contain the parameter: KeyName')

    def test_T4083_with_keyname(self):
        try:
            self.a1_r1.fcu.ModifyInstanceKeypair(KeyName=self.keyname)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'MissingParameter', 'The request must contain the parameter: InstanceId')

    def test_T4084_without_params(self):
        try:
            self.a1_r1.fcu.ModifyInstanceKeypair()
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'MissingParameter', 'The request must contain the parameter: InstanceId')

    def test_T4085_with_invalid_params(self):
        try:
            self.a1_r1.fcu.ModifyInstanceKeypair(InstanceId='inst_id', KeyName='keyname')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'InvalidInstanceID.Malformed', "The instance ID must be in the form 'i-xxxxxx'")

    def test_T4086_with_params_from_other_account(self):
        try:
            self.a2_r1.fcu.ModifyInstanceKeypair(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], KeyName=self.keyname)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'InvalidInstanceID.NotFound', 'The instance IDs do not exist: {}'.format(self.inst_info[INSTANCE_ID_LIST][0]))
