from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import id_generator, assert_error
from qa_common_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old, delete_lbu
from qa_tina_tools.tina.setup_tools import setup_public_load_balancer


class Test_DeregisterInstancesFromLoadBalancer(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeregisterInstancesFromLoadBalancer, cls).setup_class()
        cls.lbu_name = id_generator(prefix='lb-')
        cls.inst_ids = None
        try:
            cls.inst_ids, _ = setup_public_load_balancer(cls.a1_r1, cls.lbu_name, [cls.a1_r1.config.region.az_name])
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_ids:
                delete_instances_old(cls.a1_r1, cls.inst_ids)
            delete_lbu(cls.a1_r1, cls.lbu_name)
        finally:
            super(Test_DeregisterInstancesFromLoadBalancer, cls).teardown_class()

    def test_T1546_missing_lb_name(self):
        try:
            self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(Instances=[{'InstanceId': self.inst_ids[0]}])
            try:
                self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': self.inst_ids[0]}])
            except Exception:
                pass
            assert False, 'Call should not have been successful, missing parameter'
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerName')

    def test_T1547_incorrect_lb_name(self):
        try:
            self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName='foobar', Instances=[{'InstanceId': self.inst_ids[0]}])
            try:
                self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': self.inst_ids[0]}])
            except Exception:
                pass
            assert False, 'Call should not have been successful, invalid loadbalancer name'
        except OscApiException as err:
            assert_error(err, 400, 'LoadBalancerNotFound', "There is no ACTIVE Load Balancer named 'foobar'")

    def test_T1548_missing_instances(self):
        try:
            self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=self.lbu_name)
            try:
                self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': self.inst_ids[0]}])
            except Exception:
                pass
            assert False, 'Call should not have been successful, missing parameter'
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', "The request must contain the parameter Instances")
        pass

    def test_T1549_incorrect_instances(self):
        try:
            self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': 'i-12345678'}])
            try:
                self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': self.inst_ids[0]}])
            except Exception:
                pass
            assert False, 'Call should not have been successful, invalid instance id'
        except OscApiException as err:
            assert_error(err, 400, 'InvalidInstance', 'Instance i-12345678 is not a valid instance')

    def test_T1550_lb_name_incorrect_type(self):
        try:
            self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=[self.lbu_name], Instances=[{'InstanceId': self.inst_ids[0]}])
            try:
                self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': self.inst_ids[0]}])
            except Exception:
                pass
            assert False, 'Call should not have been successful, incorrect parameter type'
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'Loadbalancer name does not have the good format')

    def test_T1551_instances_non_list_type(self):
        try:
            self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=self.lbu_name, Instances=self.inst_ids[0])
            try:
                self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': self.inst_ids[0]}])
            except Exception:
                pass
            assert False, 'Call should not have been successful, incorrect parameter type'
        except OscApiException as err:
            assert_error(err, 400, 'OWS.Error', 'Request is not valid.')

    def test_T1552_instances_incorrect_item_type(self):
        try:
            self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[self.inst_ids[0]])
            try:
                self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': self.inst_ids[0]}])
            except Exception:
                pass
            assert False, 'Call should not have been successful, incorrect parameter type'
        except OscApiException as err:
            assert_error(err, 400, 'OWS.Error', 'Request is not valid.')

    def test_T1553_correct_params(self):
        self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': self.inst_ids[0]}])
        self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': self.inst_ids[0]}])

    def test_T1554_instances_list(self):
        self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=self.lbu_name,
                                                           Instances=[{'InstanceId': self.inst_ids[0]}, {'InstanceId': self.inst_ids[1]}])
        self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.lbu_name,
                                                         Instances=[{'InstanceId': self.inst_ids[0]}, {'InstanceId': self.inst_ids[1]}])

    def test_T1555_twice(self):
        self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': self.inst_ids[0]}])
        try:
            self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': self.inst_ids[0]}])
        except OscApiException as err:
            assert_error(err, 400, 'InvalidInstance', 'Instance {} is not a valid instance'.format(self.inst_ids[0]))
        finally:
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': self.inst_ids[0]}])

    def test_T1556_extra_parameter(self):
        self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': self.inst_ids[0]}],
                                                           ExtraParam='foobar')
        self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.lbu_name, Instances=[{'InstanceId': self.inst_ids[0]}])
