from qa_sdk_common.exceptions.osc_exceptions import OscException, OscApiException
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_LoadBalancer(OscTestSuite):

    def test_T1830_create_delete(self):
        name = id_generator(prefix='lbu-crud-')
        num = 20
        create_errors = 0
        delete_errors = 0
        create_sucess = 0
        delete_success = 0
        for i in range(num):
            try:
                resp = None
                resp = create_load_balancer(self.a1_r1, name + str(i))
                create_sucess += 1
            except OscApiException:
                create_errors += 1
            except OscException:
                create_errors += 1
            finally:
                try:
                    if resp:
                        delete_lbu(self.a1_r1, name + str(i))
                        delete_success += 1
                except OscException:
                    delete_errors += 1

        # TODO: rm time.sleep
        # without sleep last lbu are not deleted on tinman (why ?)
        # bug user.gc ?
        assert create_errors == 0
        assert delete_errors == 0
        assert create_sucess == num
        assert delete_success == create_sucess

    def test_T4582_create_read_delete_oapi(self):
        num = 20
        create_errors = 0
        delete_errors = 0
        create_sucess = 0
        delete_success = 0
        for _ in range(num):
            try:
                name = id_generator(prefix='lbu-')
                resp = None
                resp = self.a1_r1.oapi.CreateLoadBalancer(
                    Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                    LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
                create_sucess += 1
            except OscApiException:
                self.a1_r1.oapi.ReadLoadBalancers(Filters={'LoadBalancerNames': [name]})
                create_errors += 1
            finally:
                try:
                    if resp:
                        delete_lbu(self.a1_r1, name )
                        delete_success += 1
                except OscException:
                    delete_errors += 1
        assert create_errors == 0
        assert delete_errors == 0
        assert create_sucess == num
        assert delete_success == create_sucess
