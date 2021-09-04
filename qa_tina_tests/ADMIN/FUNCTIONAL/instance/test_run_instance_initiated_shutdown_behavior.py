
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST

class Test_RunInstances(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_RunInstances, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_RunInstances, cls).teardown_class()

    def test_T5941_run_instance_with_shutdown_behavior_terminate(self):
        inst_info = None
        try:
            inst_info = create_instances(self.a1_r1 ,state='running', iisb='terminate')
            inst_id = inst_info[INSTANCE_ID_LIST][0]
            ret = self.a1_r1.fcu.DescribeInstanceAttribute(Attribute='instanceInitiatedShutdownBehavior', InstanceId=inst_id)
            assert ret.response.instanceInitiatedShutdownBehavior.value == 'terminate'
            ret = self.a1_r1.intel.instance.get(owner=self.a1_r1.config.account.account_id, id=inst_id)
            assert ret.response.result.state == 'running'
            assert ret.response.result.ustate == 'running'
            if inst_info:
                self.a1_r1.fcu.TerminateInstances(InstanceId=[inst_id])
                self.a1_r1.intel.instance.gc()
                ret = self.a1_r1.intel.instance.get(owner=self.a1_r1.config.account.account_id, id=inst_id)
                assert ret.response.result.state == 'terminated'
                assert ret.response.result.ustate == 'terminated'
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
