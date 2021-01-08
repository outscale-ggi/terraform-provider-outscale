from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_load_balancer, create_vpc_old
from qa_tina_tools.tools.tina.delete_tools import delete_subnet, delete_vpc_old, delete_instances_old, delete_lbu
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


class Test_RegisterInstancesWithLoadBalancer(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_RegisterInstancesWithLoadBalancer, cls).setup_class()

        cls.subnet_id = None
        cls.name = None
        cls.name_2 = None
        cls.inst_id_acct_2 = None
        cls.subnet_id = None
        cls.subnet_id_2 = None
        cls.vpc_id = cls.vpc_id_2 = None
        cls.instance_id = None
        cls.inst_id_pub = None
        cls.inst_id_pub_2 = None
        cls.instance_id_vpc_2 = None
        try:
            cls.name = id_generator(prefix='lbu-')
            create_load_balancer(cls.a1_r1, cls.name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                 availability_zones=[cls.a1_r1.config.region.az_name])
            ret = create_vpc_old(cls.a1_r1, Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc_id = ret.response.vpc.vpcId
            ret = cls.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_1_0_24'), VpcId=cls.vpc_id)
            cls.subnet_id = ret.response.subnet.subnetId
            cls.name_2 = id_generator(prefix='lbu-')
            create_load_balancer(cls.a1_r1, cls.name_2, listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                                 scheme='internal', subnets=[cls.subnet_id])
            cls.omi = cls.a1_r1.config.region.get_info(constants.CENTOS7)
            ret = create_vpc_old(cls.a1_r1, Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc_id_2 = ret.response.vpc.vpcId
            ret = cls.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_1_0_24'), VpcId=cls.vpc_id_2)
            cls.subnet_id_2 = ret.response.subnet.subnetId
            ret = cls.a1_r1.fcu.RunInstances(ImageId=cls.omi, MinCount=1, MaxCount=1, SubnetId=cls.subnet_id_2)
            cls.instance_id_vpc_2 = ret.response.instancesSet[0].instanceId
            ret = cls.a1_r1.fcu.RunInstances(ImageId=cls.omi, MinCount=1, MaxCount=1, SubnetId=cls.subnet_id)
            cls.instance_id = ret.response.instancesSet[0].instanceId
            ret = cls.a1_r1.fcu.RunInstances(ImageId=cls.omi, MinCount=1, MaxCount=1)
            cls.inst_id_pub = ret.response.instancesSet[0].instanceId
            ret = cls.a1_r1.fcu.RunInstances(ImageId=cls.omi, MinCount=1, MaxCount=1)
            cls.inst_id_pub_2 = ret.response.instancesSet[0].instanceId
            ret = cls.a2_r1.fcu.RunInstances(ImageId=cls.omi, MinCount=1, MaxCount=1)
            cls.inst_id_acct_2 = ret.response.instancesSet[0].instanceId
            wait_instances_state(cls.a1_r1, [cls.instance_id, cls.inst_id_pub, cls.inst_id_pub_2], state='running')
            wait_instances_state(cls.a2_r1, [cls.inst_id_acct_2], state='running')
        except Exception as error:
            cls.teardown_class()
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.name:
                delete_lbu(cls.a1_r1, cls.name)
            if cls.name_2:
                delete_lbu(cls.a1_r1, cls.name_2)
            delete_instances_old(cls.a2_r1, [cls.inst_id_acct_2])
            delete_instances_old(cls.a1_r1, [cls.instance_id, cls.inst_id_pub, cls.inst_id_pub_2, cls.instance_id_vpc_2])
            if cls.subnet_id:
                delete_subnet(cls.a1_r1, cls.subnet_id)
            if cls.subnet_id_2:
                delete_subnet(cls.a1_r1, cls.subnet_id_2)
            if cls.vpc_id:
                delete_vpc_old(cls.a1_r1, cls.vpc_id)
            if cls.vpc_id_2:
                delete_vpc_old(cls.a1_r1, cls.vpc_id_2)
        finally:
            super(Test_RegisterInstancesWithLoadBalancer, cls).teardown_class()

    def test_T1280_without_param(self):
        try:
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer()
            assert False, "call should not have been successful, must contain param LoadBalancerName"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "The request must contain the parameter LoadBalancerName"

    def test_T1283_without_instances(self):
        try:
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name)
            assert False, "call should not have been successful, must contain param instances"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "The request must contain the parameter Instances"

    def test_T1290_with_lb_public_and_instance_in_vpc(self):
        try:
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name, Instances=[{'InstanceId': self.instance_id}])
            assert False, "call should not have been successful, bad instances name"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "LBU and Instance networks are different. LBU is in: Public Cloud, while Instance is in: %s" % self.vpc_id

    def test_T1285_with_valid_and_invalid_instance(self):
        try:
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name,
                                                             Instances=[{'InstanceId': self.inst_id_pub}, {'InstanceId': 'toto'}])
            assert False, "call should not have been successful, bad instances name"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "Invalid ID received: toto. Expected format: i-"

    def test_T1289_with_invalid_instance(self):
        try:
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name, Instances=[{'InstanceId': 'toto'}])
            assert False, "call should not have been successful, bad instances name"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "Invalid ID received: toto. Expected format: i-"

    def test_T1294_with_multi_invalid_instances(self):
        try:
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name, Instances=[{'InstanceId': 'tutu'}, {'InstanceId': 'toto'}])
            assert False, "call should not have been successful, bad instances name"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "Invalid ID received: tutu. Expected format: i-"

    def test_T1296_without_lb(self):
        try:
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(Instances=[{'InstanceId': self.instance_id}])
            assert False, "call should not have been successful, must contain param LoadBalancerName"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "The request must contain the parameter LoadBalancerName"

    def test_T1297_with_invalid_lb_name(self):
        try:
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(Instances=[{'InstanceId': self.instance_id}], LoadBalancerName='toto')
            assert False, "call should not have been successful, must contain valid param LoadBalancerName"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "There is no ACTIVE Load Balancer named 'toto'"

    def test_T1299_with_deleted_lb(self):
        try:
            name = id_generator(prefix='lbu-')
            create_load_balancer(self.a1_r1, name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                 availability_zones=[self.a1_r1.config.region.az_name])
            delete_lbu(self.a1_r1, lbu_name=name)
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(Instances=[{'InstanceId': self.inst_id_pub}], LoadBalancerName=name)
            assert False, "call should not have been successful, must contain valid param LoadBalancerName"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "There is no ACTIVE Load Balancer named '%s'" % name

    def test_T1288_with_stopped_instance(self):
        ret = self.a1_r1.fcu.RunInstances(ImageId=self.omi, MinCount=1, MaxCount=1)
        instance_stopped = ret.response.instancesSet[0].instanceId
        wait_instances_state(self.a1_r1, [instance_stopped], state='running')
        self.a1_r1.fcu.StopInstances(InstanceId=[instance_stopped], Force=True)
        wait_instances_state(self.a1_r1, [instance_stopped], state='stopped')
        self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name, Instances=[{'InstanceId': instance_stopped}])
        self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=self.name, Instances=[{'InstanceId': instance_stopped}])
        self.a1_r1.fcu.TerminateInstances(InstanceId=[instance_stopped])
        wait_instances_state(self.a1_r1, [instance_stopped], state='terminated')

    def test_T1287_with_terminated_instance(self):
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.omi, MinCount=1, MaxCount=1)
            instance_terminated = ret.response.instancesSet[0].instanceId
            wait_instances_state(self.a1_r1, [instance_terminated], state='running')
            self.a1_r1.fcu.StopInstances(InstanceId=[instance_terminated], Force=True)
            self.a1_r1.fcu.TerminateInstances(InstanceId=[instance_terminated])
            wait_instances_state(self.a1_r1, [instance_terminated], state='terminated')
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name, Instances=[{'InstanceId': instance_terminated}])
            assert False, "call should not have been successful, instance is terminated"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "Instances are not in a valid state for this operation: %s. State: terminated" % instance_terminated

    def test_T1292_with_instance_from_another_vpc(self):
        try:
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name, Instances=[{'InstanceId': self.instance_id_vpc_2}])
            assert False, "call should not have been successful, must contain valid instance"
        except OscApiException as err:
            assert err.message == "LBU and Instance networks are different. LBU is in: Public Cloud, while Instance is in: %s" % self.vpc_id_2

    def test_T1291_with_lb_in_vpc_and_instance_public(self):
        try:
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name_2, Instances=[{'InstanceId': self.inst_id_pub}])
            assert False, "call should not have been successful, must contain valid instance"
        except OscApiException as err:
            assert err.message == "LBU and Instance networks are different. LBU is in: %s, while Instance is in: Public Cloud" % self.vpc_id

    def test_T1293_with_instance_from_another_account(self):
        try:
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name_2, Instances=[{'InstanceId': self.inst_id_acct_2}])
            assert False, "call should not have been successful, must contain valid instance"
        except OscApiException as err:
            assert err.message == "Instance %s is not a valid instance" % self.inst_id_acct_2

    def test_T1281_with_valid_instance(self):
        self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name, Instances=[{'InstanceId': self.inst_id_pub}])
        self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=self.name, Instances=[{'InstanceId': self.inst_id_pub}])

    def test_T1295_with_instance_registered(self):
        self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name, Instances=[{'InstanceId': self.inst_id_pub}])
        self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name, Instances=[{'InstanceId': self.inst_id_pub}])
        self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=self.name, Instances=[{'InstanceId': self.inst_id_pub}])

    def test_T1282_with_multiple_valid_instances(self):
        self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name,
                                                         Instances=[{'InstanceId': self.inst_id_pub}, {'InstanceId': self.inst_id_pub_2}])
        self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=self.name,
                                                           Instances=[{'InstanceId': self.inst_id_pub}, {'InstanceId': self.inst_id_pub_2}])

    def test_T1702_with_instance_ids_incorrect_type(self):
        try:
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.name, Instances=[self.instance_id])
            assert False, "call should not have been successful, incorrect instances type"
        except OscApiException as err:
            assert_error(err, 400, 'OWS.Error', 'Request is not valid.')
