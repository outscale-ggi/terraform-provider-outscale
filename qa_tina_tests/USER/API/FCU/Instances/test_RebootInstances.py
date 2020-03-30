# pylint: disable=missing-docstring

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances, terminate_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
import string


class Test_RebootInstances(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_RebootInstances, cls).setup_class()
        cls.info = None

    @classmethod
    def teardown_class(cls):
        super(Test_RebootInstances, cls).teardown_class()

    def setup_method(self, method):
        super(Test_RebootInstances, self).setup_method(method)
        self.info = None

    def teardown_method(self, method):
        try:
            if self.info:
                delete_instances(self.a1_r1, self.info)
        finally:
            super(Test_RebootInstances, self).teardown_method(method)

    def test_T1644_without_ids(self):
        try:
            self.a1_r1.fcu.RebootInstances()
            assert False, 'Call without ids should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: InstanceIDs')

    def test_T1645_with_empty_ids(self):
        try:
            self.a1_r1.fcu.RebootInstances(InstanceId=[])
            assert False, 'Call without ids should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: InstanceIDs')

    def test_T1646_with_invalid_ids(self):
        try:
            self.a1_r1.fcu.RebootInstances(InstanceId=['foo'])
            assert False, 'Call with invalid ids should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.Malformed', 'Invalid ID received: foo. Expected format: i-')

    def test_T1647_from_running(self):
        self.info = create_instances(self.a1_r1, state='running')
        ret = self.a1_r1.fcu.RebootInstances(InstanceId=self.info[INSTANCE_ID_LIST])
        assert ret.response.osc_return

    def test_T1648_from_ready(self):
        self.info = create_instances(self.a1_r1, state='ready')
        ret = self.a1_r1.fcu.RebootInstances(InstanceId=self.info[INSTANCE_ID_LIST])
        assert ret.response.osc_return

    def test_T1649_from_stop(self):
        self.info = create_instances(self.a1_r1, state='running')
        inst_id_list = self.info[INSTANCE_ID_LIST]
        self.a1_r1.fcu.StopInstances(InstanceId=inst_id_list, Force=False)
        try:
            self.a1_r1.fcu.RebootInstances(InstanceId=inst_id_list)
            assert False, 'Call with stopping instance should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'IncorrectInstanceState',
                         "Instances are not in a valid state for this operation: {}. State: stopping".format(inst_id_list[0]))

    def test_T1650_from_stopped(self):
        self.info = create_instances(self.a1_r1, state='running')
        inst_id_list = self.info[INSTANCE_ID_LIST]
        stop_instances(self.a1_r1, inst_id_list)
        try:
            self.a1_r1.fcu.RebootInstances(InstanceId=inst_id_list)
            assert False, 'Call with stopped instance should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'IncorrectInstanceState',
                         "Instances are not in a valid state for this operation: {}. State: stopped".format(inst_id_list[0]))

    def test_T1651_from_terminated(self):
        self.info = create_instances(self.a1_r1, state='running')
        inst_id_list = self.info[INSTANCE_ID_LIST]
        terminate_instances(self.a1_r1, inst_id_list)
        del self.info[INSTANCE_SET]
        try:
            self.a1_r1.fcu.RebootInstances(InstanceId=inst_id_list)
            assert False, 'Call with terminated instance should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'IncorrectInstanceState',
                         "Instances are not in a valid state for this operation: {}. State: terminated".format(inst_id_list[0]))

    def test_T1652_with_unknown_param(self):
        self.info = create_instances(self.a1_r1, state='ready')
        ret = self.a1_r1.fcu.RebootInstances(InstanceId=self.info[INSTANCE_ID_LIST], foo='bar')
        # not exactly expected behavoir, but T2 ignore unknown param
        assert ret.response.osc_return

    def test_T1653_with_unknown_ids(self):
        inst_id = id_generator(prefix='i-', size=8, chars=string.digits)
        try:
            self.a1_r1.fcu.RebootInstances(InstanceId=[inst_id])
            assert False, 'Call with invalid ids should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound', "The instance IDs do not exist: {}".format(inst_id))

    def test_T1654_with_instance_from_another_account(self):
        info = create_instances(self.a2_r1, state='running')
        inst_id_list = info[INSTANCE_ID_LIST]
        try:
            self.a1_r1.fcu.RebootInstances(InstanceId=inst_id_list)
            assert False, 'Call with instance from another account should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound', "The instance IDs do not exist: {}".format(inst_id_list[0]))
        finally:
            delete_instances(self.a2_r1, info)

    def test_T1655_with_multiple_valid_instances(self):
        self.info = create_instances(self.a1_r1, state='ready', nb=2)
        ret = self.a1_r1.fcu.RebootInstances(InstanceId=self.info[INSTANCE_ID_LIST])
        assert ret.response.osc_return

    def test_T1656_with_multiple_valid_and_invalid_instances(self):
        inst_id = id_generator(prefix='i-', size=8, chars=string.digits)
        self.info = create_instances(self.a1_r1, state='ready')
        inst_id_list = self.info[INSTANCE_ID_LIST]
        try:
            self.a1_r1.fcu.RebootInstances(InstanceId=inst_id_list + [inst_id])
            assert False, 'Call with invalid instance should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound', "The instance IDs do not exist: {}".format(inst_id))
            wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=inst_id_list, state='running', threshold=1)
