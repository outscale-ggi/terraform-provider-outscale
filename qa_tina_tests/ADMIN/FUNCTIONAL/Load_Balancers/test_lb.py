from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import id_generator


class Test_lb(OscTestSuite):

    def test_T1945_check_gc(self):
        lb_name = id_generator('lbu')
        self.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                          LoadBalancerName=lb_name, AvailabilityZones=[self.a1_r1.config.region.az_name])

        self.a1_r1.lbu.DeleteLoadBalancer(LoadBalancerName=lb_name)

        ret = self.a1_r1.intel_lbu.lb.describe(owner=self.a1_r1.config.account.account_id)
        assert len(ret.response.result) == 1
        assert ret.response.result[0].name == lb_name
        assert ret.response.result[0].status in ['dirty', 'processing', 'dirty-processing']
        assert ret.response.result[0].deleted

        self.a1_r1.intel_lbu.control.gc(owner=self.a1_r1.config.account.account_id, name=lb_name)

        ret = self.a1_r1.intel_lbu.lb.describe(owner=self.a1_r1.config.account.account_id)
        assert len(ret.response.result) == 0
