

import time

import requests

from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.check_tools import wait_lbu_backend_state
from qa_tina_tools.tina.setup_tools import start_test_http_server
from qa_tina_tools.tools.tina.create_tools import create_instances, create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_lbu
from qa_tina_tools.tools.tina.info_keys import SECURITY_GROUP_ID, INSTANCE_ID_LIST, INSTANCE_SET, KEY_PAIR, PATH


class Test_lbu_timeout(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_lbu_timeout, cls).setup_class()
        cls.inst_info = None
        cls.lbu_name = None
        cls.dns_name = None
        cls.registered = False
        try:
            cls.inst_info = create_instances(cls.a1_r1, 1, state='ready')
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=cls.inst_info[SECURITY_GROUP_ID], IpProtocol='tcp',
                                                        FromPort=80, ToPort=80, CidrIp=Configuration.get('cidr', 'allips'))
            start_test_http_server(cls.inst_info[INSTANCE_SET][0]['ipAddress'], cls.inst_info[KEY_PAIR][PATH],
                              cls.a1_r1.config.region.get_info(constants.CENTOS_USER))
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
            super(Test_lbu_timeout, cls).teardown_class()

    def setup_method(self, method):
        super(Test_lbu_timeout, self).setup_method(method)
        self.lbu_name = None
        self.dns_name = None
        self.registered = False
        try:
            name = id_generator('lbu')
            self.dns_name = create_load_balancer(self.a1_r1, name).response.CreateLoadBalancerResult.DNSName
            self.lbu_name = name
            self.a1_r1.lbu.ConfigureHealthCheck(LoadBalancerName=self.lbu_name,
                                                HealthCheck={'HealthyThreshold': 2,
                                                             'Interval': 10,
                                                             'Target': 'HTTP:80/',
                                                             'Timeout': 5,
                                                             'UnhealthyThreshold': 2})
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=self.lbu_name,
                                                             Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][0]}])
            self.registered = True
            wait_lbu_backend_state(self.a1_r1, self.lbu_name)
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
            super(Test_lbu_timeout, self).teardown_method(method)


    def test_T4444_valid_timeout(self):
        self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=self.lbu_name,
                                                    LoadBalancerAttributes={'ConnectionSettings': {'IdleTimeout': 15}})
        time.sleep(15)
        ret = requests.get("http://{}/timeout".format(self.dns_name))
        assert ret.status_code == 200


    def test_T4445_invalid_timeout(self):
        self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=self.lbu_name,
                                                    LoadBalancerAttributes={'ConnectionSettings': {'IdleTimeout': 5}})
        time.sleep(15)
        ret = requests.get("http://{}/timeout".format(self.dns_name))
        assert ret.status_code == 504
