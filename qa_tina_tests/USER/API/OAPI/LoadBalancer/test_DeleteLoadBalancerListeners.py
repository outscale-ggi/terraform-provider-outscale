
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_oapi_error
from qa_tina_tests.USER.API.OAPI.LoadBalancer.LoadBalancer import LoadBalancer, validate_load_balancer_global_form


class Test_DeleteLoadBalancerListeners(LoadBalancer):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteLoadBalancerListeners, cls).setup_class()
        cls.lb_name = None
        cls.ports = [8080, 8081, 8082]
        try:
            cls.lb_name = id_generator(prefix='lbu-')
            cls.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=cls.lb_name, SubregionNames=[cls.a1_r1.config.region.az_name],
            )
            cls.a1_r1.oapi.CreateLoadBalancerListeners(LoadBalancerName=cls.lb_name,
                                                       Listeners=[{'BackendPort': cls.ports[0],
                                                                   'LoadBalancerProtocol': 'HTTP',
                                                                   'LoadBalancerPort': cls.ports[0]}])
            cls.a1_r1.oapi.CreateLoadBalancerListeners(LoadBalancerName=cls.lb_name,
                                                       Listeners=[{'BackendPort': cls.ports[1], 'LoadBalancerProtocol': 'HTTP',
                                                                   'LoadBalancerPort': cls.ports[1]}])
            cls.a1_r1.oapi.CreateLoadBalancerListeners(LoadBalancerName=cls.lb_name,
                                                       Listeners=[{'BackendPort': cls.ports[2],
                                                                   'LoadBalancerProtocol': 'HTTP',
                                                                   'LoadBalancerPort': cls.ports[2],
                                                                   'BackendProtocol': 'HTTP'}])
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.lb_name:
                try:
                    cls.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=cls.lb_name)
                except:
                    print('Could not delete lbu')
        finally:
            super(Test_DeleteLoadBalancerListeners, cls).teardown_class()

    def test_T2617_empty_param(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancerListeners()
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2618_with_no_port(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancerListeners(LoadBalancerName='Tata')
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2619_with_invalid_port(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancerListeners(LoadBalancerName=self.lb_name, LoadBalancerPorts=[123456879])
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5028')
        try:
            self.a1_r1.oapi.DeleteLoadBalancerListeners(LoadBalancerName=self.lb_name, LoadBalancerPorts=[4210])
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5028')

    def test_T3549_valid_dry_run(self):
        self.a1_r1.oapi.DeleteLoadBalancerListeners(LoadBalancerName=self.lb_name, LoadBalancerPorts=[8080], DryRun=True)

    @pytest.mark.tag_sec_confidentiality
    def test_T3550_with_other_user(self):
        try:
            self.a2_r1.oapi.DeleteLoadBalancerListeners(LoadBalancerName=self.lb_name, LoadBalancerPorts=[8080])
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5030')

    def test_T2620_valid_case(self):
        lb = self.a1_r1.oapi.DeleteLoadBalancerListeners(LoadBalancerName=self.lb_name, LoadBalancerPorts=[8080]).response.LoadBalancer
        validate_load_balancer_global_form(lb)
        lb = self.a1_r1.oapi.DeleteLoadBalancerListeners(LoadBalancerName=self.lb_name,
                                                         LoadBalancerPorts=[self.ports[1], self.ports[2]]).response.LoadBalancer
        validate_load_balancer_global_form(lb)
