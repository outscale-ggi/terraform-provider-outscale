


import time

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


class Test_IISB(OscTestSuite):

    def test_T203_shutdown_with_iisb_restart(self):
        inst_info = None
        try:
            inst_info = create_instances(osc_sdk=self.a1_r1, iisb='restart')
            self.a1_r1.fcu.StopInstances(InstanceId=inst_info[INSTANCE_ID_LIST], Force=True)
            time.sleep(5)
            wait_instances_state(self.a1_r1, instance_id_list=inst_info[INSTANCE_ID_LIST], state='running')
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T202_shutdown_with_iisb_terminate(self):
        inst_info = None
        try:
            inst_info = create_instances(osc_sdk=self.a1_r1, iisb='terminate')
            self.a1_r1.fcu.StopInstances(InstanceId=inst_info[INSTANCE_ID_LIST], Force=True)
            wait_instances_state(self.a1_r1, instance_id_list=inst_info[INSTANCE_ID_LIST], state='terminated')
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
