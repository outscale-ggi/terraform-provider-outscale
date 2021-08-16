from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina import info_keys
from qa_tina_tools.tools.tina.delete_tools import delete_instances


class Test_get_requirements(OscTinaTest):

    def test_T5841_with_valid_param(self):
        inst_info = None
        try:
            inst_info = create_instances(self.a1_r1)
            ret = self.a1_r1.intel.slot.get_requirements(vm_id=[inst_info[info_keys.INSTANCE_ID_LIST][0]])
            #TODO check response
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

