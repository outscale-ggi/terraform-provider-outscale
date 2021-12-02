import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina import info_keys
from qa_tina_tools.tools.tina.delete_tools import delete_instances


class Test_get_requirements(OscTinaTest):

    def test_T5841_with_valid_param(self):
        inst_info = None
        try:
            inst_info = create_instances(self.a1_r1)
            resp = self.a1_r1.intel.slot.get_requirements(vm_id=[inst_info[info_keys.INSTANCE_ID_LIST][0]][0]).response
            assert hasattr(resp, "result")
            pytest.fail("Remove known error")
        except AssertionError:
            known_error('TINA-6694', 'get_requirements does not work')
        except OscApiException as error:
            if error.message == "Internal error.":
                known_error('TINA-6694', 'get_requirements does not work')
            else:
                raise error
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
