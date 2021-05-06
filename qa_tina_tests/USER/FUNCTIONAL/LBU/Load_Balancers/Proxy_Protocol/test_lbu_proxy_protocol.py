

import os
import time

import requests

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tina.check_tools import wait_lbu_backend_state
from qa_tina_tools.tina.setup_tools import start_test_http_server
from qa_tina_tools.tools.tina.create_tools import create_instances, create_load_balancer, create_self_signed_cert
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_lbu
from qa_tina_tools.tools.tina.info_keys import SECURITY_GROUP_ID, INSTANCE_ID_LIST, INSTANCE_SET, KEY_PAIR, PATH


class Test_lbu_proxy_protocol(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_lbu_proxy_protocol, cls).setup_class()
        cls.inst_info = None
        cls.crtpath = None
        cls.keypath = None
        cls.cert_arn = None
        cls.cert_name = None
        try:
            cls.inst_info = create_instances(cls.a1_r1, 1, state='ready')
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=cls.inst_info[SECURITY_GROUP_ID], IpProtocol='tcp',
                                                        FromPort=80, ToPort=80, CidrIp=Configuration.get('cidr', 'allips'))
            start_test_http_server(cls.inst_info[INSTANCE_SET][0]['ipAddress'], cls.inst_info[KEY_PAIR][PATH],
                                   cls.a1_r1.config.region.get_info(constants.CENTOS_USER))

            cls.crtpath, cls.keypath = create_self_signed_cert()
            key = open(cls.keypath).read()
            cert = open(cls.crtpath).read()
            ret_up = cls.a1_r1.eim.UploadServerCertificate(ServerCertificateName=id_generator(prefix='cc-'), CertificateBody=cert, PrivateKey=key)
            cls.cert_arn = ret_up.response.UploadServerCertificateResult.ServerCertificateMetadata.Arn
            cls.cert_name = ret_up.response.UploadServerCertificateResult.ServerCertificateMetadata.ServerCertificateName
        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.cert_name:
                try:
                    cls.a1_r1.eim.DeleteServerCertificate(ServerCertificateName=cls.cert_name)
                except Exception:
                    print('Could not delete server certificate')
            if cls.crtpath:
                os.remove(cls.crtpath)
            if cls.keypath:
                os.remove(cls.keypath)
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_lbu_proxy_protocol, cls).teardown_class()

    def exec_proxy_protocol_test(self, listener, https_error=False):
        lbu_name = None
        dns_name = None
        registered = False
        try:
            name = id_generator('lbu')
            dns_name = create_load_balancer(self.a1_r1,
                                            name,
                                            listeners=[listener]).response.CreateLoadBalancerResult.DNSName
            lbu_name = name
            self.a1_r1.lbu.ConfigureHealthCheck(LoadBalancerName=lbu_name,
                                                HealthCheck={'HealthyThreshold': 2,
                                                             'Interval': 10,
                                                             'Target': 'HTTP:80/',
                                                             'Timeout': 5,
                                                             'UnhealthyThreshold': 2})
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=lbu_name,
                                                             Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][0]}])
            registered = True
            policy_name = id_generator('policy')
            self.a1_r1.lbu.CreateLoadBalancerPolicy(LoadBalancerName=lbu_name, PolicyName=policy_name, PolicyTypeName="ProxyProtocolPolicyType")
            self.a1_r1.lbu.SetLoadBalancerPoliciesForBackendServer(LoadBalancerName=lbu_name, InstancePort='80', PolicyNames=[policy_name])
            time.sleep(60)  # Wait config
            try:
                wait_lbu_backend_state(self.a1_r1, lbu_name)
                if https_error:
                    assert False, "remove known error"
            except AssertionError:
                wait_lbu_backend_state(self.a1_r1, lbu_name, expected_state='OutService')
                known_error('TINA-6472', 'errors for load balancer with proxy_protocol_https')
            except OscApiException as error:
                assert_error(error, 500, 'InternalFailure', 'Internal Error')
                known_error('TINA-6472', 'errors for load balancer with proxy_protocol_https')

            ret = self.a1_r1.intel_lbu.lb.get(owner=self.a1_r1.config.account.account_id,
                                              names=[lbu_name])
            inst_id = ret.response.result[0].lbu_instance
            ret = self.a1_r1.intel.instance.find(id=inst_id)
            lbu_ip = ret.response.result[0].private_ip
            protocol = 'http'
            if listener['LoadBalancerPort'] == '443':
                protocol = 'https'
            for _ in range(5):
                try:
                    ret = requests.get("{}://{}/proxy_protocol".format(protocol, dns_name), verify=listener['verify'])
                    break
                except Exception:
                    print('Could not reach load balancer')
            assert ret.status_code == 200
            expexted_text = []
            for i in self.a1_r1.config.region.get_info(constants.MY_IP):
                expexted_text.append("{} -> {}".format(i.split('/')[0], lbu_ip))
            assert ret.text in expexted_text
        finally:
            if registered:
                self.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=lbu_name,
                                                                   Instances=[{'InstanceId': self.inst_info[INSTANCE_ID_LIST][0]}])
            if lbu_name:
                delete_lbu(self.a1_r1, lbu_name)

    def test_T4443_proxy_protocol_tcp(self):
        self.exec_proxy_protocol_test(listener={'InstancePort': '80',
                                                'LoadBalancerPort': '80',
                                                'Protocol': 'TCP',
                                                'verify': False})

    def test_T4535_proxy_protocol_http(self):
        self.exec_proxy_protocol_test(listener={'InstancePort': '80',
                                                'LoadBalancerPort': '80',
                                                'Protocol': 'HTTP',
                                                'verify': False})

    def test_T4536_proxy_protocol_ssl(self):
        self.exec_proxy_protocol_test(listener={'InstancePort': '80',
                                                'LoadBalancerPort': '443',
                                                'Protocol': 'SSL',
                                                'SSLCertificateId': self.cert_arn,
                                                'verify': False}
                                      )
    def test_T4537_proxy_protocol_https(self):
        self.exec_proxy_protocol_test(listener={'InstancePort': '80',
                                                'LoadBalancerPort': '443',
                                                'Protocol': 'HTTPS',
                                                'SSLCertificateId': self.cert_arn,
                                                'verify': False}, https_error=True)
