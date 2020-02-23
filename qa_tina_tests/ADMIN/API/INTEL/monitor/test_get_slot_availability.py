from qa_common_tools.test_base import OscTestSuite


class Test_get_slot_availability(OscTestSuite):

    def test_T3567_with_instance_types_filter(self):
        ret = self.a1_r1.intel.monitor.get_slot_availability(instance_types='t2.small')
        assert ret.response.result

    def test_T3568_with_account_filter(self):
        ret = self.a1_r1.intel.monitor.get_slot_availability(account=self.a1_r1.config.account.account_id)
        assert ret.response.result

    def test_T3569_with_pz_filter(self):
        ret = self.a1_r1.intel.monitor.get_slot_availability(pz='in2')
        assert ret.response.result

    def test_T3570_with_combined_filter(self):
        ret = self.a1_r1.intel.monitor.get_slot_availability(instance_types='t2.small', account=self.a1_r1.config.account.account_id)
        assert ret.response.result
