from qa_test_tools.test_base import OscTestSuite


class Test_find(OscTestSuite):

    def test_T5764_without_param(self):
        resp = self.a1_r1.intel.agents.find().response
        for agent in resp.result:
            self.logger.debug(agent.display())
            assert not agent.device  # ?
            if agent.type in ['vpc', 'vpng', 'ring']:
                assert agent.vm_id
                assert agent.name.startswith('fw-master')
            elif  agent.type in ['vm', 'dl', 'filer', 'kms', 'copy', 'dns']:
                assert not agent.vm_id
                assert agent.name
            assert agent.version
            assert agent.last_start_date.dt
            assert agent.last_heartbeat_date.dt
            assert not agent.reset_date # ?
            assert not agent.last_error_report # ?
            assert agent.state == 'active'
