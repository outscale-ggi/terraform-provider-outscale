from qa_test_tools.test_base import OscTestSuite

class Test_agents_get_heartbeat(OscTestSuite):

    def test_T5794_agents_get_heartbeat(self):
        agent_name = self.a1_r1.intel.hardware.get_servers(state='READY').response.result[0].name
        resp = self.a1_r1.intel.agents.find(name=agent_name).response
        last_heartbeat_date = resp.result[0].last_heartbeat_date
        self.a1_r1.intel.agents.get_heartbeat(agent_name=agent_name)
        resp = self.a1_r1.intel.agents.find(name=agent_name).response
        updated_last_heartbeat_date = resp.result[0].last_heartbeat_date
        assert last_heartbeat_date != updated_last_heartbeat_date
