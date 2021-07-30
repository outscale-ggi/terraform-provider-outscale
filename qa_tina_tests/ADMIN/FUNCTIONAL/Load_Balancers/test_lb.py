import time

from qa_test_tools.misc import id_generator
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_lb(OscTinaTest):

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

    def test_T5032_check_release_eip_after_delete(self):
        lb_names = []
        eip_values = []
        ips = []
        for _ in range(3):
            ret_lb = None
            try:
                lb_name = id_generator(prefix='lbu-')
                ret_lb = self.a1_r1.oapi.CreateLoadBalancer(
                    Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                    LoadBalancerName=lb_name, SubregionNames=[self.a1_r1.config.region.az_name],
                )
                lb_names.append(lb_name)
                count = 0
                while count < 5:
                    time.sleep(20)
                    ret = self.a1_r1.intel.netimpl.firewall.find_firewalls(filters={'resource': ret_lb.response.LoadBalancer.DnsName.split('.')[0]})
                    if ret.response.result:
                        break
                    count += 1
                if count == 5:
                    raise OscTestException('Could not find lbu firewall')
                ret = self.a1_r1.intel.tag.find(resource=ret.response.result[0].vm, key='osc.fcu.eip.auto-attach')
                eip_values.append(ret.response.result[0].value)
            finally:
                if ret_lb:
                    delete_lbu(self.a1_r1, lbu_name=lb_name)
        time.sleep(60)
        ret = self.a1_r1.intel.address.describe(owner=self.a1_r1.intel.user.get_details(username='ows.elb@outscale.com').response.result.username)
        for i in ret.response.result.results:
            ips.append(i.ip)
        for eip in eip_values:
            assert not eip in ips
