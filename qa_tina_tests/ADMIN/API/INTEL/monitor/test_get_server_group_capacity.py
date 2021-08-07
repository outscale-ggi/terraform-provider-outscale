import pytest

from qa_tina_tools.test_base import OscTinaTest


@pytest.mark.region_admin
class Test_get_server_group_capacity(OscTinaTest):

    def test_T5837_with_instance_types_filter(self):
        ret = self.a1_r1.intel.monitor.get_server_group_capacity()
        for res in ret.response.result:
            assert hasattr(res, 'gpu_models'), "missing item 'gpu_models'."
            gpu_models = getattr(res, 'gpu_models')
            assert hasattr(gpu_models, 'available'), "missing item 'available'."
            assert hasattr(gpu_models, 'total'), "missing item 'total'."
            assert hasattr(gpu_models, 'used'), "missing item 'used'."
