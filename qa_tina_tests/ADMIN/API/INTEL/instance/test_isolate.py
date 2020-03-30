from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances, terminate_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


class Test_isolate(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        super(Test_isolate, cls).setup_class()
        try:
            cls.inst_info = create_instances(cls.a1_r1, nb=3, state='running')
            stop_instances(cls.a1_r1, [cls.inst_info[INSTANCE_ID_LIST][1]], wait=False)
            terminate_instances(cls.a1_r1, [cls.inst_info[INSTANCE_ID_LIST][2]], wait=False)
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
                for inst_id in cls.inst_info[INSTANCE_ID_LIST]:
                    try:
                        cls.a1_r1.intel.instance.unisolate(owner=cls.a1_r1.config.account.account_id, vmid=inst_id)
                    except:
                        pass
                delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_isolate, cls).teardown_class()

    def test_T3259_running_instance(self):
        self.a1_r1.intel.instance.isolate(owner=self.a1_r1.config.account.account_id, vmid=self.inst_info[INSTANCE_ID_LIST][0])

    def test_T3260_stopped_instance(self):
        wait_instances_state(self.a1_r1, [self.inst_info[INSTANCE_ID_LIST][1]], 'stopped')
        self.a1_r1.intel.instance.isolate(owner=self.a1_r1.config.account.account_id, vmid=self.inst_info[INSTANCE_ID_LIST][1])

    def test_T3261_terminated_instance(self):
        try:
            wait_instances_state(self.a1_r1, [self.inst_info[INSTANCE_ID_LIST][2]], 'terminated')
            self.a1_r1.intel.instance.isolate(owner=self.a1_r1.config.account.account_id, vmid=self.inst_info[INSTANCE_ID_LIST][2])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-state')
