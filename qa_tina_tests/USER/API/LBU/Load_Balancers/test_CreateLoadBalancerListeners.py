from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import id_generator, assert_error
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_CreateLoadBalancerListeners(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateLoadBalancerListeners, cls).setup_class()
        cls.lbu_name = id_generator('lbu-')
        cls.ret_create = None
        try:
            cls.ret_create = create_load_balancer(cls.a1_r1, cls.lbu_name, availability_zones=[cls.a1_r1.config.region.az_name],
                                                  listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}])
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret_create:
                delete_lbu(cls.a1_r1, cls.lbu_name)
        finally:
            super(Test_CreateLoadBalancerListeners, cls).teardown_class()

    def test_T593_with_empty_ssl_certificate_id(self):
        self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=self.lbu_name,
                                                   Listeners=[{'InstancePort': 8080,
                                                               'Protocol': 'HTTP',
                                                               'LoadBalancerPort': 8080,
                                                               'SSLCertificateId': None}])

    def test_T1302_with_only_lb_name(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=self.lbu_name)
            assert False, "call should not have been successful, must contain Listeners param"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "The request must contain the parameter Listeners"

    def test_T1301_with_invalid_lb_name(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName='toto',
                                                       Listeners=[{'InstancePort': 8080, 'Protocol': 'HTTP', 'LoadBalancerPort': 8080}])
            assert False, "call should not have been successful, invalid LoadBalancerName param"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "There is no ACTIVE Load Balancer named 'toto'"

    def test_T1278_with_invalid_instance_protocol(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=self.lbu_name,
                                                       Listeners=[{'InstancePort': 8080,
                                                                   'Protocol': 'HTTP',
                                                                   'LoadBalancerPort': 8080,
                                                                   'InstanceProtocol': 'toto'}])
            assert False, "call should not have been successful, invalid instance protocol"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "Invalid protocol 'toto', must be one of SSL, UDP, HTTP, TCP, HTTPS"

    def test_T1277_with_invalid_lb_port(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=self.lbu_name,
                                                       Listeners=[{'InstancePort': 8080, 'Protocol': 'HTTP', 'LoadBalancerPort': 65536}])
            assert False, "call should not have been successful, invalid LoadBalancerPort"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "Load balancer port must be in 1-65535 inclusive"

    def test_T1276_with_invalid_protocol(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=self.lbu_name,
                                                       Listeners=[{'InstancePort': 8080, 'Protocol': 'toto', 'LoadBalancerPort': 8080}])
            assert False, "call should not have been successful, invalid protocol"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "Invalid protocol 'toto', must be one of SSL, UDP, HTTP, TCP, HTTPS"

    def test_T1275_with_invalid_instance_port(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=self.lbu_name,
                                                       Listeners=[{'InstancePort': 0, 'Protocol': 'HTTP', 'LoadBalancerPort': 2000}])
            assert False, "call should not have been successful, invalid InstancePort"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "1 validation error detected: Value '0' at 'listeners.1.member.instancePort' \
failed to satisfy constraint: Member must have value greater than or equal to 1"

        try:
            self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=self.lbu_name,
                                                       Listeners=[{'InstancePort': 65536, 'Protocol': 'HTTP', 'LoadBalancerPort': 1025}])
            assert False, "call should not have been successful, invalid InstancePort"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "1 validation error detected: Value '65536' at 'listeners.1.member.instancePort' \
failed to satisfy constraint: Member must have value less than or equal to 65535"

    def test_T1279_with_valid_param(self):
        self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=self.lbu_name,
                                                   Listeners=[{'InstancePort': 8081, 'Protocol': 'HTTP', 'LoadBalancerPort': 8081}])
        self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=self.lbu_name,
                                                   Listeners=[{'InstancePort': 8082,
                                                               'Protocol': 'HTTP',
                                                               'LoadBalancerPort': 8082,
                                                               'InstanceProtocol': 'HTTP'}])
        self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=self.lbu_name,
                                                   Listeners=[{'InstancePort': 8083, 'Protocol': 'UDP', 'LoadBalancerPort': 8083}])

    def test_T4006_with_missing_certificate_id(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=self.lbu_name,
                                                       Listeners=[{'InstancePort': 2222, 'Protocol': 'SSL', 'LoadBalancerPort': 2222}])
            assert False, "call should not have been successful, missing certificate id"
        except OscApiException as err:
            assert_error(err, 400, 'CertificateNotFound', None)
