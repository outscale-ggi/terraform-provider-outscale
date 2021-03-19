from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.create_tools import create_load_balancer, create_vpc_old
from qa_tina_tools.tools.tina.delete_tools import delete_lbu
from qa_tina_tools.tools.tina.wait_tools import wait_subnets_state, wait_load_balancer_state


class Test_CreateLoadBalancer(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_id = None
        cls.igw_id = None
        cls.subnet_id = None
        cls.subnet_id_2 = None
        cls.sg_id = None
        cls.sg_id_2 = None
        cls.sg_id_3 = None
        cls.lb_name = None
        super(Test_CreateLoadBalancer, cls).setup_class()
        try:
            ret = create_vpc_old(cls.a1_r1, Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc_id = ret.response.vpc.vpcId
            ret = cls.a1_r1.fcu.CreateInternetGateway()
            cls.igw_id = ret.response.internetGateway.internetGatewayId
            ret = cls.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=cls.igw_id, VpcId=cls.vpc_id)
            ret = cls.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_1_0_24'), VpcId=cls.vpc_id)
            cls.subnet_id = ret.response.subnet.subnetId
            ret = cls.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_2_0_24'), VpcId=cls.vpc_id)
            cls.subnet_id_2 = ret.response.subnet.subnetId
            wait_subnets_state(cls.a1_r1, [cls.subnet_id, cls.subnet_id_2], state='available')
            ret = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test', GroupName='sg1', VpcId=cls.vpc_id)
            cls.sg_id = ret.response.groupId
            ret = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test', GroupName='sg2', VpcId=cls.vpc_id)
            cls.sg_id_2 = ret.response.groupId
            ret = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test', GroupName='sg3')
            cls.sg_id_3 = ret.response.groupId
            lb_name = id_generator(prefix='lbu-')
            create_load_balancer(cls.a1_r1, lb_name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                 availability_zones=[cls.a1_r1.config.region.az_name])
            cls.lb_name = lb_name
        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.lb_name:
                try:
                    delete_lbu(cls.a1_r1, cls.lb_name)
                except:
                    print('Could not delete lbu.')
            if cls.sg_id_3:
                try:
                    cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.sg_id_3)
                except:
                    print('Could not delete security group.')
            if cls.vpc_id:
                try:
                    cleanup_vpcs(cls.a1_r1, vpc_id_list=[cls.vpc_id], force=True)
                except:
                    print('Could not delete vpcs.')
        finally:
            super(Test_CreateLoadBalancer, cls).teardown_class()

    def test_T567_with_existing_name_diff_param(self):
        try:
            create_load_balancer(self.a1_r1, self.lb_name, listeners=[{'InstancePort': 65534, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                 availability_zones=[self.a1_r1.config.region.az_name])
            assert False, "Call should not have been successful, same name and different params"
        except Exception as error:
            assert_error(error, 400, 'DuplicateLoadBalancerName',
                         "Load Balancer named '{}' already exists and it is configured with different parameters.".format(self.lb_name))

    def test_T607_with_existing_name_same_param(self):
        create_load_balancer(self.a1_r1, self.lb_name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                             availability_zones=[self.a1_r1.config.region.az_name])

    def test_T743_without_param(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancer()
            assert False, "Call should not have been successful, request must contain LoadBalancer name"
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerName')

    def test_T745_with_invalid_availability_zone(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                              LoadBalancerName='lbu1')
            assert False, "Call should not have been successful, request must contain valid availabilityZone"
        except OscApiException as err:
            assert_error(err, 400, 'MissingParameter', 'Insufficient parameters provided out of: AvailabilityZones, subnets. Expected at least: 1')
        try:
            self.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                              LoadBalancerName='lbu1', AvailabilityZones=['toto'])
            assert False, "Call should not have been successful, request must contain valid availabilityZone"
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', "'toto' is not a valid availability zone")
        try:
            self.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                              LoadBalancerName='lbu1', AvailabilityZones=['in-west-2a', 'toto'])
            assert False, "Call should not have been successful, request must contain valid availabilityZone"
        except OscApiException as err:
            assert_error(err, 400, 'NotImplemented', 'Attaching load balancer to multiple availability zones is not yet implemented')

    def test_T746_with_valid_listener(self):
        name = id_generator(prefix='lbu-')
        create_load_balancer(self.a1_r1, name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                             availability_zones=[self.a1_r1.config.region.az_name])
        delete_lbu(self.a1_r1, name)
        name = id_generator(prefix='lbu-')
        create_load_balancer(self.a1_r1, name,
                             listeners=[{'InstancePort': 1, 'Protocol': 'HTTP', 'LoadBalancerPort': 25, 'InstanceProtocol': 'HTTP'}],
                             availability_zones=[self.a1_r1.config.region.az_name])
        delete_lbu(self.a1_r1, name)
        name = id_generator(prefix='lbu-')
        create_load_balancer(self.a1_r1, name,
                             listeners=[{'InstancePort': 80, 'Protocol': 'TCP', 'LoadBalancerPort': 1024, 'InstanceProtocol': 'TCP'}],
                             availability_zones=[self.a1_r1.config.region.az_name])
        delete_lbu(self.a1_r1, name)
        name = id_generator(prefix='lbu-')
        create_load_balancer(self.a1_r1, name,
                             listeners=[{'InstancePort': 80, 'Protocol': 'UDP', 'LoadBalancerPort': 1024, 'InstanceProtocol': 'UDP'}],
                             availability_zones=[self.a1_r1.config.region.az_name])
        delete_lbu(self.a1_r1, name)
        name = id_generator(prefix='lbu-')
        create_load_balancer(self.a1_r1, name, availability_zones=[self.a1_r1.config.region.az_name])
        delete_lbu(self.a1_r1, name)

    def test_T747_with_invalid_listener(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 0, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                              LoadBalancerName='lbu1', AvailabilityZones=[self.a1_r1.config.region.az_name])
            assert False, "Call should not have been successful, request must contain valid listener param"
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'Invalid port number, port must be in the range 1-65535')
        try:
            self.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 65536, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                              LoadBalancerName='lbu1', AvailabilityZones=[self.a1_r1.config.region.az_name])
            assert False, "Call should not have been successful, request must contain valid listener param"
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'Invalid port number, port must be in the range 1-65535')
        try:
            self.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 1, 'Protocol': 'HTTP', 'LoadBalancerPort': 65536}],
                                              LoadBalancerName='lbu1', AvailabilityZones=[self.a1_r1.config.region.az_name])
            assert False, "Call should not have been successful, request must contain valid listener param"
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'Load balancer port must be in 1-65535 inclusive')
        try:
            self.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 1, 'Protocol': 'UDP', 'LoadBalancerPort': 65536}],
                                              LoadBalancerName='lbu1', AvailabilityZones=[self.a1_r1.config.region.az_name])
            assert False, "Call should not have been successful, request must contain valid listener param"
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'Load balancer port must be in 1-65535 inclusive')

    def test_T748_with_invalid_loadbalancer_name(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                              LoadBalancerName='totototototototototototototototototototo',
                                              AvailabilityZones=[self.a1_r1.config.region.az_name])
            assert False, "Call should not have been successful, request must contain valid LoadBalancer name"
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', "Length of parameter 'LoadBalancerName' is invalid: 40. Expected: set([(1, 32)]).")
        try:
            self.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                              LoadBalancerName='lbu_-1', AvailabilityZones=[self.a1_r1.config.region.az_name])
            assert False, "Call should not have been successful, request must contain valid LoadBalancer name"
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'Loadbalancer name must contain only alphanumeric characters or hyphens')
        try:
            self.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                              LoadBalancerName='ééééééééé', AvailabilityZones=[self.a1_r1.config.region.az_name])
            assert False, "Call should not have been successful, request must contain valid LoadBalancer name"
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'Loadbalancer name must contain only alphanumeric characters or hyphens')

    def test_T749_with_valid_security_group(self):
        name = id_generator(prefix='lbu-')
        create_load_balancer(self.a1_r1, name, listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}], scheme='internal',
                             subnets=[self.subnet_id], sg=[self.sg_id])
        delete_lbu(self.a1_r1, name)
        name = id_generator(prefix='lbu-')
        create_load_balancer(self.a1_r1, name, listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}], scheme='internal',
                             subnets=[self.subnet_id], sg=[self.sg_id, self.sg_id_2])
        delete_lbu(self.a1_r1, name)
        name = id_generator(prefix='lbu-')
        create_load_balancer(self.a1_r1, name, listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'UDP'}], scheme='internal',
                             subnets=[self.subnet_id], sg=[self.sg_id_2])
        delete_lbu(self.a1_r1, name)

    def test_T750_with_invalid_security_group(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancer(LoadBalancerName='lb1',
                                              Listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                                              Scheme='internal', Subnets=[self.subnet_id], SecurityGroups=['toto'])
            assert False, "Call should not have been successful, request must contain valid security group param"
        except OscApiException as err:
            assert_error(err, 400, 'InvalidSecurityGroup', None)
            # TODO check error message
        try:
            self.a1_r1.lbu.CreateLoadBalancer(LoadBalancerName='lb1',
                                              Listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                                              Scheme='internal', Subnets=[self.subnet_id], SecurityGroups=[self.sg_id, 'toto'])
            assert False, "Call should not have been successful, request must contain valid security group param"
        except OscApiException as err:
            assert_error(err, 400, 'InvalidSecurityGroup', None)

    def test_T751_with_valid_subnet(self):
        name = id_generator(prefix='lbu-')
        create_load_balancer(self.a1_r1, name, listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}], scheme='internal',
                             subnets=[self.subnet_id])
        delete_lbu(self.a1_r1, name)

    def test_T753_with_valid_scheme(self):
        name = id_generator(prefix='lbu-')
        try:
            create_load_balancer(self.a1_r1, name, listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                                 scheme='internet-facing', subnets=[self.subnet_id])
            delete_lbu(self.a1_r1, name)
        except Exception as error:
            print((str(error)))

    def test_T754_with_all_param_valid(self):
        name = id_generator(prefix='lbu-')
        create_load_balancer(self.a1_r1, name, listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                             availability_zones=[self.a1_r1.config.region.az_name])
        delete_lbu(self.a1_r1, name)
        name = id_generator(prefix='lbu-')
        create_load_balancer(self.a1_r1, name, listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}], scheme='internal',
                             subnets=[self.subnet_id], tags=[{'Key': 'tag_key', 'Value': 'tag_value'}])
        delete_lbu(self.a1_r1, name)
        name = id_generator(prefix='lbu-')
        create_load_balancer(self.a1_r1, name, listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'UDP'}], scheme='internal',
                             subnets=[self.subnet_id], tags=[{'Key': 'tag_key', 'Value': 'tag_value'}])
        delete_lbu(self.a1_r1, name)

    def test_T756_with_invalid_scheme(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancer(Scheme='toto', Listeners=[{'InstancePort': 1, 'Protocol': 'HTTP', 'LoadBalancerPort': 65535}],
                                              LoadBalancerName='lbu1', AvailabilityZones=[self.a1_r1.config.region.az_name], SecurityGroups=['sg1'])
            assert False, "Call should not have been successful, request must contain valid scheme param"
        except OscApiException as err:
            assert_error(err, 400, 'InvalidParameterValue',
                         "Value of parameter \'Scheme\' is not valid: toto. Supported values: internal, internet-facing")

    def test_T758_with_invalid_subnet(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancer(LoadBalancerName='lb1',
                                              Listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                                              Scheme='internal', Subnets=['toto'])
            assert False, "Call should not have been successful, request must contain valid subnet param"
        except OscApiException as err:
            assert_error(err, 400, 'InvalidSubnetID.Malformed', 'Invalid ID received: toto. Expected format: subnet-')
        try:
            self.a1_r1.lbu.CreateLoadBalancer(LoadBalancerName='lb1',
                                              Listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}], Scheme='internal',
                                              Subnets=[self.subnet_id, 'toto'])
            assert False, "Call should not have been successful, request must contain valid subnet param"
        except OscApiException as err:
            assert_error(err, 400, 'InvalidSubnetID.Malformed', 'Invalid ID received: toto. Expected format: subnet-')

    def test_T1342_without_listener(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancer(LoadBalancerName='lbu1')
            wait_load_balancer_state(self.a1_r1, load_balancer_name_list=['lbu1'])
            delete_lbu(self.a1_r1, 'lbu1')
            wait_load_balancer_state(self.a1_r1, load_balancer_name_list=['lbu1'], cleanup=True)
            assert False, "Call should not have been successful, request must contain Listener param"
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter Listeners')

    def test_T3047_without_subnet(self):
        try:
            self.a1_r1.lbu.CreateLoadBalancer(LoadBalancerName='lb1',
                                              Listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}], Scheme='internal')
            wait_load_balancer_state(self.a1_r1, load_balancer_name_list=['lbu1'])
            delete_lbu(self.a1_r1, 'lbu1')
            wait_load_balancer_state(self.a1_r1, load_balancer_name_list=['lbu1'], cleanup=True)
            assert False, "Call should not have been successful, request must contain Subnets param"
        except OscApiException as err:
            assert_error(err, 400, 'MissingParameter', 'Insufficient parameters provided out of: AvailabilityZones, subnets. Expected at least: 1')

    def test_T1416_private_internal_with_wrong_security_group(self):
        try:
            create_load_balancer(self.a1_r1, 'T1416', listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                                 scheme='internal', subnets=[self.subnet_id], sg=[self.sg_id_3])
            wait_load_balancer_state(self.a1_r1, load_balancer_name_list=['T1416'])
            delete_lbu(self.a1_r1, 'T1416')
            wait_load_balancer_state(self.a1_r1, load_balancer_name_list=['T1416'], cleanup=True)
            assert False, "Call should not have been successful, security group not in vpc"
        except OscApiException as err:
            assert_error(err, 400, 'InvalidSecurityGroup', None)

    def test_T1413_name_starting_with_dash(self):
        try:
            lb_name = '-T1413'
            create_load_balancer(self.a1_r1, lb_name, listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                                 scheme='internal', subnets=[self.subnet_id], sg=[self.sg_id])
            wait_load_balancer_state(self.a1_r1, load_balancer_name_list=[lb_name])
            delete_lbu(self.a1_r1, lb_name)
            wait_load_balancer_state(self.a1_r1, load_balancer_name_list=[lb_name], cleanup=True)
            assert False, "Call should not have been successful, lbu name starts with '-'"
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'Loadbalancer name cannot begin or end with a hyphen')

    def test_T1544_name_ending_with_dash(self):
        try:
            lb_name = 'T1544-'
            create_load_balancer(self.a1_r1, lb_name, listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                                 scheme='internal', subnets=[self.subnet_id], sg=[self.sg_id])
            wait_load_balancer_state(self.a1_r1, load_balancer_name_list=[lb_name])
            delete_lbu(self.a1_r1, lb_name)
            wait_load_balancer_state(self.a1_r1, load_balancer_name_list=[lb_name], cleanup=True)
            assert False, "Call should not have been successful, lbu name ends with '-'"
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'Loadbalancer name cannot begin or end with a hyphen')

    def test_T1415_private_internal_without_security_group(self):
        create_load_balancer(self.a1_r1, 'T1415', listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                             scheme='internal', subnets=[self.subnet_id])
        wait_load_balancer_state(self.a1_r1, load_balancer_name_list=['T1415'])
        delete_lbu(self.a1_r1, 'T1415')
        wait_load_balancer_state(self.a1_r1, load_balancer_name_list=['T1415'], cleanup=True)

    def test_T1424_private_internal_with_security_group(self):
        create_load_balancer(self.a1_r1, 'T1424', listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                             scheme='internal', subnets=[self.subnet_id], sg=[self.sg_id])
        delete_lbu(self.a1_r1, 'T1424')

    def test_T1425_private_without_security_group(self):
        create_load_balancer(self.a1_r1, 'T1425', listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                             subnets=[self.subnet_id])
        wait_load_balancer_state(self.a1_r1, load_balancer_name_list=['T1425'])
        delete_lbu(self.a1_r1, 'T1425')

    def test_T1426_private_with_security_group(self):
        create_load_balancer(self.a1_r1, 'T1426', listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                             subnets=[self.subnet_id], sg=[self.sg_id])
        delete_lbu(self.a1_r1, 'T1426')

    def test_T1452_public_with_security_group(self):
        try:
            create_load_balancer(self.a1_r1, 'T1452', listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                                 availability_zones=[self.a1_r1.config.region.az_name], sg=[self.sg_id])
            wait_load_balancer_state(self.a1_r1, load_balancer_name_list=['T1452'])
            delete_lbu(self.a1_r1, 'T1452')
            wait_load_balancer_state(self.a1_r1, load_balancer_name_list=['T1452'], cleanup=True)
            assert False, "Call should not have been successful, specified security group for public lbu"
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'Security groups are only applicable on ELB in VPC')

    def test_T1453_public_without_security_group(self):
        create_load_balancer(self.a1_r1, 'T1453', listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                             availability_zones=[self.a1_r1.config.region.az_name])
        wait_load_balancer_state(self.a1_r1, load_balancer_name_list=['T1453'])
        delete_lbu(self.a1_r1, 'T1453')
        wait_load_balancer_state(self.a1_r1, load_balancer_name_list=['T1453'], cleanup=True)

    def test_T4672_name_with_special_character(self):
        name = 'ABCD§EFGH'
        try:
            create_load_balancer(self.a1_r1, name, listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                                 availability_zones=[self.a1_r1.config.region.az_name])
            wait_load_balancer_state(self.a1_r1, load_balancer_name_list=[name])
            delete_lbu(self.a1_r1, name)
            wait_load_balancer_state(self.a1_r1, load_balancer_name_list=[name], cleanup=True)
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'Loadbalancer name must contain only alphanumeric characters '
                                                      'or hyphens')

    def test_T5074_with_long_name(self):
        try:
            name = id_generator(prefix='lbu-', size=33)
            create_load_balancer(self.a1_r1, name,
                                 listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}],
                                 availability_zones=[self.a1_r1.config.region.az_name])
            assert False, "Call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', "Length of parameter 'LoadBalancerName' is invalid: 37. Expected: set([(1, 32)]).")
