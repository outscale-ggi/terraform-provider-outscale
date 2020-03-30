# -*- coding:utf-8 -*-

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_oapi_error
from qa_tina_tests.USER.API.OAPI.LoadBalancer.LoadBalancer import LoadBalancer, validate_load_balancer_global_form


class Test_CreateLoadBalancerListeners(LoadBalancer):

    @classmethod
    def setup_class(cls):
        super(Test_CreateLoadBalancerListeners, cls).setup_class()
        cls.lb_name = None
        cls.setup_error = False
        try:
            cls.lb_name = id_generator(prefix='lbu-')
            cls.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=cls.lb_name, SubregionNames=[cls.a1_r1.config.region.az_name],
            )
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.lb_name:
                try:
                    cls.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=cls.lb_name)
                except:
                    pass
        finally:
            super(Test_CreateLoadBalancerListeners, cls).teardown_class()

    def test_T2609_with_only_lb_name(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerListeners(LoadBalancerName=self.lb_name)
            assert False, "call should not have been successful, must contain Listeners param"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2610_with_invalid_instance_protocol(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerListeners(LoadBalancerName=self.lb_name,
                                                        Listeners=[{'BackendPort': 8080,
                                                                    'LoadBalancerProtocol': 'HTTP',
                                                                    'LoadBalancerPort': 8080,
                                                                    'BackendProtocol': 'toto'}])
            assert False, "call should not have been successful, invalid instance protocol"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4095')

    def test_T2611_with_invalid_lb_name(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerListeners(LoadBalancerName='toto',
                                                        Listeners=[{'BackendPort': 8080, 'LoadBalancerProtocol': 'HTTP',
                                                                    'LoadBalancerPort': 8080}])
            assert False, "call should not have been successful, invalid LoadBalancerName param"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5030')

    def test_T2612_with_invalid_lb_port(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerListeners(LoadBalancerName=self.lb_name,
                                                        Listeners=[{'BackendPort': 8080, 'LoadBalancerProtocol': 'HTTP',
                                                                    'LoadBalancerPort': 0}])
            assert False, "call should not have been successful, invalid LoadBalancerPort"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4037')

        try:
            self.a1_r1.oapi.CreateLoadBalancerListeners(LoadBalancerName=self.lb_name,
                                                        Listeners=[{'BackendPort': 8080, 'LoadBalancerProtocol': 'HTTP',
                                                                    'LoadBalancerPort': 65536}])
            assert False, "call should not have been successful, invalid LoadBalancerPort"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4037')

    def test_T2613_with_invalid_protocol(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerListeners(LoadBalancerName=self.lb_name,
                                                        Listeners=[{'BackendPort': 8080, 'LoadBalancerProtocol': 'toto',
                                                                    'LoadBalancerPort': 8080}])
            assert False, "call should not have been successful, invalid protocol"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4095')

    def test_T2614_with_invalid_instance_port(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerListeners(LoadBalancerName=self.lb_name,
                                                        Listeners=[{'BackendPort': 0, 'LoadBalancerProtocol': 'HTTP',
                                                                    'LoadBalancerPort': 2000}])
            assert False, "call should not have been successful, invalid BackendPort"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4095')

        try:
            self.a1_r1.oapi.CreateLoadBalancerListeners(LoadBalancerName=self.lb_name,
                                                        Listeners=[
                                                            {'BackendPort': 65536, 'LoadBalancerProtocol': 'HTTP',
                                                             'LoadBalancerPort': 1025}])
            assert False, "call should not have been successful, invalid BackendPort"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4095')

    def test_T2615_with_valid_param(self):
        lb = self.a1_r1.oapi.CreateLoadBalancerListeners(LoadBalancerName=self.lb_name,
                                                         Listeners=[{'BackendPort': 8081, 'LoadBalancerProtocol': 'HTTP',
                                                                     'LoadBalancerPort': 8081}]).response.LoadBalancer
        validate_load_balancer_global_form(lb)
        lb = self.a1_r1.oapi.CreateLoadBalancerListeners(LoadBalancerName=self.lb_name,
                                                         Listeners=[{'BackendPort': 8082,
                                                                     'LoadBalancerProtocol': 'HTTP',
                                                                     'LoadBalancerPort': 8082,
                                                                     'BackendProtocol': 'HTTP'}]).response.LoadBalancer
        validate_load_balancer_global_form(lb)

    def test_T2616_with_empty_ssl_certificate_id(self):
        lb = self.a1_r1.oapi.CreateLoadBalancerListeners(LoadBalancerName=self.lb_name,
                                                         Listeners=[{'BackendPort': 8080,
                                                                     'LoadBalancerProtocol': 'HTTP',
                                                                     'LoadBalancerPort': 8080,
                                                                     'ServerCertificateId': ''}]).response.LoadBalancer
        validate_load_balancer_global_form(lb)
