
import pytest

from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state

class Test_RunInstances(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_RunInstances, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_RunInstances, cls).teardown_class()

    @pytest.mark.region_admin
    def test_T5941_run_instance_with_shutdown_behavior_terminate(self):
        inst_info = None
        try:
            inst_info = create_instances(self.a1_r1 ,state='running', iisb='terminate')
            inst_id = inst_info[INSTANCE_ID_LIST][0]
            self.a1_r1.fcu.StopInstances(InstanceId=[inst_id])
            wait_instances_state(self.a1_r1, [inst_id], 'terminated')
            self.a1_r1.intel.instance.gc(immediate=True)
            wait_instances_state(self.a1_r1, [inst_id], cleanup=True)
            inst_info[INSTANCE_ID_LIST] = []
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    @pytest.mark.region_admin
    def test_T5942_run_instance_then_stop_and_terminate_it(self):
        inst_info = None
        try:
            inst_info = create_instances(self.a1_r1 ,state='running')
            inst_id = inst_info[INSTANCE_ID_LIST][0]
            self.a1_r1.fcu.StopInstances(InstanceId=[inst_id])
            wait_instances_state(self.a1_r1, [inst_id], 'stopped')
            self.a1_r1.fcu.TerminateInstances(InstanceId=[inst_id])
            wait_instances_state(self.a1_r1, [inst_id], 'terminated')
            self.a1_r1.intel.instance.gc(immediate=True)
            wait_instances_state(self.a1_r1, [inst_id], cleanup=True)
            inst_info[INSTANCE_ID_LIST] = []
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
