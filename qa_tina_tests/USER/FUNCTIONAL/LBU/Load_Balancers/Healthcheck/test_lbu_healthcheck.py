# pylint: disable=missing-docstring

import time

from qa_common_tools.config.configuration import Configuration
from qa_common_tools.constants import CENTOS_USER
from qa_common_tools.misc import id_generator
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tina.check_tools import wait_lbu_backend_state
from qa_tina_tools.tools.tina.create_tools import create_instances, create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_lbu
from qa_tina_tools.tools.tina.info_keys import SECURITY_GROUP_ID, INSTANCE_ID_LIST, INSTANCE_SET, KEY_PAIR, PATH
from qa_tina_tools.tina.setup_tools import start_test_http_server

class Test_lbu_healthcheck(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_lbu_healthcheck, cls).setup_class()
        cls.inst_info = None
        cls.lbu_name = None
        cls.registered = False
        try:
            cls.inst_info = create_instances(cls.a1_r1, 1, state='ready')
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=cls.inst_info[SECURITY_GROUP_ID], IpProtocol='tcp',
                                                        FromPort=80, ToPort=80, CidrIp=Configuration.get('cidr', 'allips'))
            start_test_http_server(cls.inst_info[INSTANCE_SET][0]['ipAddress'], cls.inst_info[KEY_PAIR][PATH],
                              cls.a1_r1.config.region.get_info(CENTOS_USER))
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_lbu_healthcheck, cls).teardown_class()

    def setup_method(self, method):
        super(Test_lbu_healthcheck, self).setup_method(method)
        self.lbu_name = None
        self.registered = False
        try:
            name = id_generator('lbu')
            create_load_balancer(self.a1_r1, name)
            self.lbu_name = name
            self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=self.lbu_name,
                                                        LoadBalancerAttributes={'ConnectionSettings': {'IdleTimeout': 20}})
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.lbu_name,
                                                             Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][0]}])
            self.registered = True
        except:
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.registered:
                self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=self.lbu_name,
                                                                   Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][0]}])
            if self.lbu_name:
                delete_lbu(self.a1_r1, self.lbu_name)
        finally:
            super(Test_lbu_healthcheck, self).teardown_method(method)


    def test_T4438_healthcheck_invalid_uri(self):
        self.a1_r1.lbu.ConfigureHealthCheck(LoadBalancerName=self.lbu_name,
                                            HealthCheck={'HealthyThreshold': 2,
                                                         'Interval': 10,
                                                         'Target': 'HTTP:80/foo',
                                                         'Timeout': 5,
                                                         'UnhealthyThreshold': 2})
        time.sleep(15) # wait config
        wait_lbu_backend_state(self.a1_r1, self.lbu_name, expected_state='OutOfService')
        time.sleep(10*2 + 15) # wait 2 health check + padding
        wait_lbu_backend_state(self.a1_r1, self.lbu_name, expected_state='OutOfService', threshold=10)

    def test_T4439_healthcheck_error_500_on_backend(self):
        self.a1_r1.lbu.ConfigureHealthCheck(LoadBalancerName=self.lbu_name,
                                            HealthCheck={'HealthyThreshold': 2,
                                                         'Interval': 10,
                                                         'Target': 'HTTP:80/500',
                                                         'Timeout': 5,
                                                         'UnhealthyThreshold': 2})
        time.sleep(15) # wait config
        wait_lbu_backend_state(self.a1_r1, self.lbu_name, expected_state='OutOfService')
        time.sleep(10*2 + 15) # wait 2 health check + padding
        wait_lbu_backend_state(self.a1_r1, self.lbu_name, expected_state='OutOfService', threshold=10)

    def test_T4441_healthcheck_valid_timeout(self):
        self.a1_r1.lbu.ConfigureHealthCheck(LoadBalancerName=self.lbu_name,
                                            HealthCheck={'HealthyThreshold': 2,
                                                         'Interval': 15,
                                                         'Target': 'HTTP:80/timeout',
                                                         'Timeout': 13,
                                                         'UnhealthyThreshold': 2})
        time.sleep(15) # wait config
        wait_lbu_backend_state(self.a1_r1, self.lbu_name)
        time.sleep(15*2 + 15) # wait 2 health check + padding
        wait_lbu_backend_state(self.a1_r1, self.lbu_name, threshold=10)

    def test_T4442_healthcheck_invalid_timeout(self):
        self.a1_r1.lbu.ConfigureHealthCheck(LoadBalancerName=self.lbu_name,
                                            HealthCheck={'HealthyThreshold': 2,
                                                         'Interval': 15,
                                                         'Target': 'HTTP:80/timeout',
                                                         'Timeout': 7,
                                                         'UnhealthyThreshold': 2})
        time.sleep(15) # wait config
        wait_lbu_backend_state(self.a1_r1, self.lbu_name, expected_state='OutOfService')
        time.sleep(15*2 + 15) # wait 2 health check + padding
        wait_lbu_backend_state(self.a1_r1, self.lbu_name, expected_state='OutOfService', threshold=10)
