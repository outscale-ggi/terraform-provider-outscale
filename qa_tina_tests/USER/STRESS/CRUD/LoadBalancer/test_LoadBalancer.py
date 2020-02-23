from osc_common.exceptions.osc_exceptions import OscException, OscApiException
from qa_common_tools.misc import id_generator
from qa_common_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_LoadBalancer(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_LoadBalancer, cls).setup_class()
        try:
            pass
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_LoadBalancer, cls).teardown_class()

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
            except OscApiException as error:
                if error.error_code == 'InternalError' and error.status_code == 500:
                    known_error('TINA-4742', 'Unexpected internal error')
                create_errors += 1
            except OscException as error:
                create_errors += 1
            finally:
                try:
                    if resp:
                        delete_lbu(self.a1_r1, name + str(i))
                        delete_success += 1
                except OscException as error:
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
            except OscApiException as error:
                self.a1_r1.oapi.ReadLoadBalancers(Filters={'LoadBalancerNames': [name]})
                if error.error_code == 'InternalError' and error.status_code == 500:
                    known_error('TINA-4742', 'Unexpected internal error')
                create_errors += 1
            finally:
                try:
                    if resp:
                        delete_lbu(self.a1_r1, name )
                        delete_success += 1
                except OscException as error:
                    delete_errors += 1
        assert create_errors == 0
        assert delete_errors == 0
        assert create_sucess == num
        assert delete_success == create_sucess
