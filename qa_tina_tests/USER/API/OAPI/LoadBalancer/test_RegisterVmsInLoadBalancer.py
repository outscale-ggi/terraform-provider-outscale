from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import assert_oapi_error
from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.misc import id_generator
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old, delete_lbu
from qa_tina_tools.tina.setup_tools import setup_private_load_balancer, setup_public_load_balancer
from qa_common_tools import constants
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs


class Test_RegisterVmsInLoadBalancer(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_RegisterVmsInLoadBalancer, cls).setup_class()
        cls.lbu_name = id_generator(prefix='lb-')
        cls.lbu_name2 = id_generator(prefix='lb-')
        cls.inst_ids = None
        cls.inst_ids2 = None
        cls.vpc_id = None
        try:
            cls.inst_ids, _ = setup_public_load_balancer(cls.a1_r1, cls.lbu_name, [cls.a1_r1.config.region.az_name],
                                                         register=False)
            cls.vpc_id, _, cls.igw_id, cls.inst_ids2, _ = setup_private_load_balancer(cls.a1_r1, cls.lbu_name2,
                                                                                      availability_zone=cls.a1_r1.config.region.az_name,
                                                                                      register=False)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            delete_lbu(cls.a1_r1, cls.lbu_name)
            delete_lbu(cls.a1_r1, cls.lbu_name2)
            if cls.inst_ids:
                delete_instances_old(cls.a1_r1, cls.inst_ids)
            if cls.inst_ids2:
                delete_instances_old(cls.a1_r1, cls.inst_ids2)
            if cls.igw_id:
                cls.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=cls.igw_id, VpcId=cls.vpc_id)
                cls.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=cls.igw_id)
            if cls.vpc_id:
                cleanup_vpcs(cls.a1_r1, vpc_id_list=[cls.vpc_id], force=True)
        finally:
            super(Test_RegisterVmsInLoadBalancer, cls).teardown_class()

    def test_T2780_without_param(self):
        try:
            self.a1_r1.oapi.RegisterVmsInLoadBalancer()
            assert False, "call should not have been successful, must contain param LoadBalancerName"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2781_without_backend_vms_ids(self):
        try:
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name)
            assert False, "call should not have been successful, must contain param backend_vms_ids"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2782_with_lb_public_and_vms_in_vpc(self):
        try:
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                      BackendVmIds=[self.inst_ids2[0]])
            assert False, "call should not have been successful, bad backend_vms_ids name"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4086')

    def test_T2783_with_valid_and_invalid_vm(self):
        try:
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                      BackendVmIds=[self.inst_ids[0], 'toto'])
            assert False, "call should not have been successful, bad backend_vms_ids name"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2784_with_invalid_vm(self):
        try:
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                      BackendVmIds=['toto'])
            assert False, "call should not have been successful, bad backend_vms_ids name"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2785_with_multi_invalid_backend_vms_ids(self):
        try:
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                      BackendVmIds=['tutu', 'toto'])
            assert False, "call should not have been successful, bad backend_vms_ids name"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2786_without_lb(self):
        try:
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(BackendVmIds=[self.inst_ids[0]])
            assert False, "call should not have been successful, must contain param LoadBalancerName"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2787_with_invalid_lb_name(self):
        try:
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(BackendVmIds=[self.inst_ids[0]], LoadBalancerName='toto')
            assert False, "call should not have been successful, must contain valid param LoadBalancerName"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5030')

    def test_T2788_with_deleted_lb(self):
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(BackendVmIds=[self.inst_ids[0]],
                                                      LoadBalancerName=name)
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5030')

    def test_T2789_with_stopped_vm(self):
        ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7),
                                          MinCount=1, MaxCount=1)
        instance_stopped = ret.response.instancesSet[0].instanceId
        wait_instances_state(self.a1_r1, [instance_stopped], state='running')
        self.a1_r1.fcu.StopInstances(InstanceId=[instance_stopped], Force=True)
        wait_instances_state(self.a1_r1, [instance_stopped], state='stopped')
        self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=[instance_stopped])
        self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name, BackendVmIds=[instance_stopped])
        self.a1_r1.fcu.TerminateInstances(InstanceId=[instance_stopped])
        wait_instances_state(self.a1_r1, [instance_stopped], state='terminated')

    def test_T2790_with_terminated_vm(self):
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7), MinCount=1, MaxCount=1)
            instance_terminated = ret.response.instancesSet[0].instanceId
            wait_instances_state(self.a1_r1, [instance_terminated], state='running')
            self.a1_r1.fcu.StopInstances(InstanceId=[instance_terminated], Force=True)
            self.a1_r1.fcu.TerminateInstances(InstanceId=[instance_terminated])
            wait_instances_state(self.a1_r1, [instance_terminated], state='terminated')
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                      BackendVmIds=[instance_terminated])
            assert False, "call should not have been successful, instance is terminated"
        except OscApiException as error:
            assert_oapi_error(error, 409, 'InvalidState', '6003')

    def test_T2791_with_vms_from_another_vpc(self):
        try:
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                      BackendVmIds=[self.inst_ids2[1]])
            assert False, "call should not have been successful, must contain valid instance"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4086')

    def test_T2792_with_lb_in_vpc_and_vms_public(self):
        try:
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name2,
                                                      BackendVmIds=[self.inst_ids[0]])
            assert False, "call should not have been successful, must contain valid instance"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4086')

    def test_T2793_with_lb_in_vpc_and_vms_in_same_vpc(self):
        assert self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name2,
                                                         BackendVmIds=[self.inst_ids2[0]])
        self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name2,
                                                    BackendVmIds=[self.inst_ids2[0]])

    def test_T2794_with_valid_vm(self):
        assert self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                         BackendVmIds=[self.inst_ids[0]])
        self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                    BackendVmIds=[self.inst_ids[0]])

    def test_T2795_with_vms_registered(self):
        try:
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                      BackendVmIds=[self.inst_ids[0]])
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                      BackendVmIds=[self.inst_ids[0]])
        finally:
            self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                        BackendVmIds=[self.inst_ids[0]])

    def test_T2796_with_multiple_valid_vms(self):
        assert self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                         BackendVmIds=self.inst_ids)
        self.a1_r1.oapi.DeregisterVmsInLoadBalancer(LoadBalancerName=self.lbu_name,
                                                    BackendVmIds=self.inst_ids)
