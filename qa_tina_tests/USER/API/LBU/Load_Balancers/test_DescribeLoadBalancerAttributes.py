from qa_common_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import assert_error, id_generator


class Test_DescribeLoadBalancerAttributes(OscTestSuite):
    
    @classmethod
    def setup_class(cls):
        super(Test_DescribeLoadBalancerAttributes, cls).setup_class()
        cls.ret1 = None
        cls.lbu_name = id_generator(prefix='lbu-')
        try:
            cls.ret1 = create_load_balancer(cls.a1_r1, cls.lbu_name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                            availability_zones=[cls.a1_r1.config.region.az_name])
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret1:
                cls.a1_r1.lbu.DeleteLoadBalancer(LoadBalancerName=cls.lbu_name)
        finally:
            super(Test_DescribeLoadBalancerAttributes, cls).teardown_class()
        
    def test_T4013_valid_param(self):
        ret = self.a1_r1.lbu.DescribeLoadBalancerAttributes(LoadBalancerName=self.lbu_name).response
        assert ret.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AccessLog
        
    def test_T4014_not_existing_name(self):
        try:
            self.a1_r1.lbu.DescribeLoadBalancerAttributes(LoadBalancerName='XXXXXX')
            self.ret1 = None
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            if error.status_code == 500 :
                known_error("TINA-4976", "DescribeLoadBalancerAttributes with non existent lbu name -> Internal error")
        assert False, 'Remove known error'

    def test_T4015_without_params(self):
        try:
            self.a1_r1.lbu.DescribeLoadBalancerAttributes()
            self.ret1 = None
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', "The request must contain the parameter LoadBalancerName")
            
    def test_T4016_with_another_account(self):
        try:
            self.a2_r1.lbu.DescribeLoadBalancerAttributes(LoadBalancerName=self.lbu_name)
            self.ret1 = None
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            if error.status_code == 500 :
                known_error("TINA-4976", 'Incorrect internal error')
            assert False, 'Remove known error'
