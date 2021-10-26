from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina.setup_tools import setup_public_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old, delete_lbu
from specs import check_oapi_error


class Test_DeregisterVmsInLoadBalancer(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_DeregisterVmsInLoadBalancer, cls).setup_class()
        cls.lbu_name = id_generator(prefix='lb-')
        cls.inst_ids = None
        try:
            cls.inst_ids, _ = setup_public_load_balancer(cls.a1_r1, cls.lbu_name, [cls.a1_r1.config.region.az_name])
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_ids:
                delete_instances_old(cls.a1_r1, cls.inst_ids)
            delete_lbu(cls.a1_r1, cls.lbu_name)
        finally:
            super(Test_DeregisterVmsInLoadBalancer, cls).teardown_class()

    def test_T2797_missing_lb_name(self):
        try:
            self.a1_r1.oapi.DeregisterVmsInLoadBalancer(BackendVmIds=[self.inst_ids[0]])
            try:
                self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                          BackendVmIds=[self.inst_ids[0]])
            except:
                print('Could not register vms in lbu')
            assert False, 'Call should not have been successful, missing parameter'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T2798_incorrect_lb_name(self):
        try:
            self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName='foobar', BackendVmIds=[self.inst_ids[0]])
            try:
                self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                          BackendVmIds=[self.inst_ids[0]])
            except:
                print('Could not register vms in lbu')
            assert False, 'Call should not have been successful, invalid loadbalancer name'
        except OscApiException as error:
            check_oapi_error(error, 5030)

    def test_T2799_missing_vms(self):
        try:
            self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name)
            try:
                self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                          BackendVmIds=[self.inst_ids[0]])
            except:
                print('Could not register vms in lbu')
            assert False, 'Call should not have been successful, missing parameter'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T2800_incorrect_vms(self):
        try:
            self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=['i-12345678'])
            try:
                self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=[self.inst_ids[0]])
            except:
                print('Could not register vms in lbu')
            assert False, 'Call should not have been successful, invalid vm id'
        except OscApiException as error:
            if error.data != 'The VmId \'{id}\' doesn\'t exist.':
                assert False, 'Remove known error'
                check_oapi_error(error, 5063, id='i-12345678')
            known_error('API-355', 'Incorrect error formatting (LoadBalancer)')

    def test_T2801_lb_name_incorrect_type(self):
        try:
            self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName=[self.lbu_name], BackendVmIds=[self.inst_ids[0]])
            try:
                self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=[self.inst_ids[0]])
            except:
                print('Could not register vms in lbu')
            assert False, 'Call should not have been successful, incorrect parameter type'
        except OscApiException as error:
            check_oapi_error(error, 4110)

    def test_T2802_vms_non_list_type(self):
        try:
            self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=self.inst_ids[0])
            try:
                self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=[self.inst_ids[0]])
            except:
                print('Could not register vms in lbu')
            assert False, 'Call should not have been successful, incorrect parameter type'
        except OscApiException as error:
            check_oapi_error(error, 4110)

    def test_T2804_correct_params(self):
        assert self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=[self.inst_ids[0]])
        self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=[self.inst_ids[0]])

    def test_T2805_vms_list(self):
        assert self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=[self.inst_ids[0], self.inst_ids[1]])
        self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=[self.inst_ids[0], self.inst_ids[1]])

    def test_T2806_twice(self):
        assert self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=[self.inst_ids[0]])
        try:
            self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=[self.inst_ids[0]])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.data != 'The VmId \'{id}\' doesn\'t exist.':
                assert False, 'Remove known error'
                check_oapi_error(error, 5063, id=self.inst_ids[0])
            known_error('API-355', 'Incorrect error formatting (LoadBalancer)')
        finally:
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=[self.inst_ids[0]])

    def test_T2807_extra_parameter(self):
        try:
            assert self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=[self.inst_ids[0]], ExtraParam='foobar')
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=[self.inst_ids[0]])
        except OscApiException as error:
            check_oapi_error(error, 3001)
