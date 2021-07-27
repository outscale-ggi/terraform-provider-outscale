from multiprocessing import Process
import multiprocessing

from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import terminate_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


INST_TYPE = 'c4.xlarge'
THREAD_NUM = 20
INST_NUM = 5
ITER = 5


def create_inst(oscsdk, procnum, return_dict, inst_type, inst_number, num_iter):
    inst_ids = []
    for _ in range(num_iter):
        inst_info = None
        try:
            inst_info = create_instances(oscsdk, nb=inst_number, inst_type=inst_type, state=None)
        except:
            # logger.exception('Could not start instances')
            print('Could not delete instances')
        if inst_info:
            inst_ids.extend(inst_info[INSTANCE_ID_LIST])
    return_dict[procnum] = inst_ids


class Test_over_fill_kvm(OscTinaTest):

    def test_T2288_verify_all_started(self):
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        threads = []
        inst_ids = []
        try:
            self.logger.info("Start workers")
            for i in range(THREAD_NUM):
                proc = Process(name="{}-{}".format('slot_test', i), target=create_inst, args=[self.a1_r1, i, return_dict, INST_TYPE, INST_NUM, ITER])
                threads.append(proc)
            for proc in threads:
                proc.start()
            self.logger.info("Wait workers")
            for proc in threads:
                proc.join()
            self.logger.info("Get results")
            for _, ids in return_dict.items():
                inst_ids.extend(ids)
            if inst_ids:
                wait_instances_state(self.a1_r1, inst_ids, state='running')
        finally:
            if inst_ids:
                terminate_instances(self.a1_r1, inst_ids)
