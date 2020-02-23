
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances, terminate_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, INSTANCE_ID_LIST
from qa_common_tools.misc import assert_error, id_generator
import string


class Test_StartInstances(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_StartInstances, cls).setup_class()
        cls.info = None

    @classmethod
    def teardown_class(cls):
        super(Test_StartInstances, cls).teardown_class()

    def setup_method(self, method):
        super(Test_StartInstances, self).setup_method(method)
        self.info = None

    def teardown_method(self, method):
        try:
            if self.info:
                delete_instances(self.a1_r1, self.info)
        finally:
            super(Test_StartInstances, self).teardown_method(method)

    def test_T1657_without_ids(self):
        try:
            self.a1_r1.fcu.StartInstances()
            assert False, 'Call without ids should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: InstanceIDs')

    def test_T1658_with_empty_ids(self):
        try:
            self.a1_r1.fcu.StartInstances(InstanceId=[])
            assert False, 'Call without ids should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: InstanceIDs')

    def test_T1659_with_invalid_ids(self):
        try:
            self.a1_r1.fcu.StartInstances(InstanceId=['foo'])
            assert False, 'Call with invalid ids should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.Malformed', 'Invalid ID received: foo. Expected format: i-')

    def test_T1660_from_running(self):
        self.info = create_instances(self.a1_r1, state='running')
        inst_id_list = self.info[INSTANCE_ID_LIST]
        ret = self.a1_r1.fcu.StartInstances(InstanceId=inst_id_list)
        assert len(ret.response.instancesSet) == len(inst_id_list)
        assert ret.response.instancesSet[0].instanceId == inst_id_list[0]
        assert ret.response.instancesSet[0].previousState.name == 'running'
        assert ret.response.instancesSet[0].currentState.name == 'running'

    def test_T1661_from_ready(self):
        self.info = create_instances(self.a1_r1, state='ready')
        inst_id_list = self.info[INSTANCE_ID_LIST]
        ret = self.a1_r1.fcu.StartInstances(InstanceId=inst_id_list)
        assert len(ret.response.instancesSet) == len(inst_id_list)
        assert ret.response.instancesSet[0].instanceId == inst_id_list[0]
        assert ret.response.instancesSet[0].previousState.name == 'running'
        assert ret.response.instancesSet[0].currentState.name == 'running'

    def test_T1662_from_stop(self):
        self.info = create_instances(self.a1_r1, state='running')
        inst_id_list = self.info[INSTANCE_ID_LIST]
        try:
            self.a1_r1.fcu.StopInstances(InstanceId=inst_id_list, Force=False)
            self.a1_r1.fcu.StartInstances(InstanceId=inst_id_list)
        except OscApiException as error:
            assert_error(error, 400, 'IncorrectInstanceState',
                         "Instances are not in a valid state for this operation: {}. State: stopping".format(inst_id_list[0]))

    def test_T1663_from_stopped(self):
        self.info = create_instances(self.a1_r1, state='running')
        inst_id_list = self.info[INSTANCE_ID_LIST]
        stop_instances(self.a1_r1, inst_id_list)
        try:
            self.a1_r1.fcu.StartInstances(InstanceId=inst_id_list)
        except OscApiException as error:
            assert_error(error, 400, 'IncorrectInstanceState',
                         "Instances are not in a valid state for this operation: {}. State: stopped".format(inst_id_list[0]))

    def test_T1664_from_terminated(self):
        self.info = create_instances(self.a1_r1, state='running')
        inst_id_list = self.info[INSTANCE_ID_LIST]
        terminate_instances(self.a1_r1, inst_id_list)
        del self.info[INSTANCE_SET]
        try:
            self.a1_r1.fcu.StartInstances(InstanceId=inst_id_list)
        except OscApiException as error:
            assert_error(error, 400, 'IncorrectInstanceState',
                         "Instances are not in a valid state for this operation: {}. State: terminated".format(inst_id_list[0]))

    def test_T1665_with_unknown_param(self):
        self.info = create_instances(self.a1_r1, state='ready')
        inst_id_list = self.info[INSTANCE_ID_LIST]
        ret = self.a1_r1.fcu.StartInstances(InstanceId=inst_id_list, foo='bar')
        # not exactly expected behavoir, but T2 ignore unknown param
        assert len(ret.response.instancesSet) == len(inst_id_list)
        assert ret.response.instancesSet[0].instanceId == inst_id_list[0]
        assert ret.response.instancesSet[0].previousState.name == 'running'
        assert ret.response.instancesSet[0].currentState.name == 'running'

    def test_T1666_with_unknown_ids(self):
        inst_id = id_generator(prefix='i-', size=8, chars=string.digits)
        try:
            self.a1_r1.fcu.StartInstances(InstanceId=[inst_id])
            assert False, 'Call with invalid ids should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound', "The instance IDs do not exist: {}".format(inst_id))

    def test_T1667_with_instance_from_another_account(self):
        info = create_instances(self.a2_r1, state='running')
        inst_id_list = info[INSTANCE_ID_LIST]
        try:
            self.a1_r1.fcu.StartInstances(InstanceId=inst_id_list)
            assert False, 'Call with instance from another account should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound', "The instance IDs do not exist: {}".format(inst_id_list[0]))
        finally:
            delete_instances(self.a2_r1, info)

    def test_T1668_with_multiple_valid_instances(self):
        self.info = create_instances(self.a1_r1, state='ready', nb=2)
        inst_id_list = self.info[INSTANCE_ID_LIST]
        ret = self.a1_r1.fcu.StartInstances(InstanceId=inst_id_list)
        assert len(ret.response.instancesSet) == len(inst_id_list)
        for inst in ret.response.instancesSet:
            assert inst.instanceId in inst_id_list
            assert inst.previousState.name == 'running'
            assert inst.currentState.name == 'running'

    def test_T1669_with_multiple_vali_and_invalid_instances(self):
        inst_id = id_generator(prefix='i-', size=8, chars=string.digits)
        self.info = create_instances(self.a1_r1, state='ready')
        inst_id_list = self.info[INSTANCE_ID_LIST]
        try:
            self.a1_r1.fcu.StartInstances(InstanceId=inst_id_list + [inst_id])
            assert False, 'Call with invalid instance should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound', "The instance IDs do not exist: {}".format(inst_id))
