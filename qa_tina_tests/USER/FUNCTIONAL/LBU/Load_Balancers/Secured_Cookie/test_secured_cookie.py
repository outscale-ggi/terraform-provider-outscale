import time
import requests
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.config import config_constants as constants

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.check_tools import wait_lbu_backend_state
from qa_tina_tools.tools.tina.create_tools import create_load_balancer, create_self_signed_cert, create_instances
from qa_tina_tools.tools.tina.info_keys import PATH, INSTANCE_ID_LIST, INSTANCE_SET, KEY_PAIR, SECURITY_GROUP_ID
from qa_tina_tools.tina.setup_tools import start_test_http_server
from qa_tina_tools.tools.tina.wait_tools import wait_load_balancer_state
from qa_tina_tools.tools.tina.delete_tools import delete_lbu
from qa_test_tools.misc import id_generator
import os


class Test_secured_cookie(OscTestSuite):

    @classmethod
    def setup_class(cls, ):
        super(Test_secured_cookie, cls).setup_class()
        cls.instance_info_a1 = None
        try:
            cls.instance_info_a1 = create_instances(cls.a1_r1, state='running')
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=cls.instance_info_a1[SECURITY_GROUP_ID], IpProtocol='tcp',
                                                        FromPort=80, ToPort=80,
                                                        CidrIp=Configuration.get('cidr', 'allips'))
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_secured_cookie, cls).teardown_class()

    def test_T4598_modify_attribute_secured_cookie_true(self):
        ret_lbu = None
        ret_up = None
        lbu_name = id_generator(prefix='lbu-')
        crtpath = None
        keypath = None
        inst_id = self.instance_info_a1[INSTANCE_ID_LIST][0]
        inst = self.instance_info_a1[INSTANCE_SET][0]
        kp_info = self.instance_info_a1[KEY_PAIR]

        try:
            start_test_http_server(inst['ipAddress'], kp_info[PATH],
                                   self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            crtpath, keypath = create_self_signed_cert()
            key = open(keypath).read()
            cert = open(crtpath).read()
            ret_up = self.a1_r1.eim.UploadServerCertificate(ServerCertificateName=id_generator(prefix='cc-'), CertificateBody=cert, PrivateKey=key)
            arn = ret_up.response.UploadServerCertificateResult.ServerCertificateMetadata.Arn
            name = ret_up.response.UploadServerCertificateResult.ServerCertificateMetadata.ServerCertificateName
            ret_lbu = create_load_balancer(self.a1_r1, lbu_name,
                                           listeners=[{'InstancePort': 80,'InstanceProtocol': 'HTTP',
                                                       'Protocol': 'HTTPS', 'LoadBalancerPort': 443,'SSLCertificateId':arn}],
                                           availability_zones=[self.a1_r1.config.region.az_name])

            dns_name = ret_lbu.response.CreateLoadBalancerResult.DNSName
            wait_load_balancer_state(self.a1_r1, [lbu_name])
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=lbu_name,
                                                             Instances=[
                                                                 {'InstanceId': inst_id}])

            self.registered = True
            wait_lbu_backend_state(self.a1_r1, lbu_name)
            ret = requests.get("https://{}/cookie".format(dns_name), verify=False)
            assert ret.headers['Set-Cookie'] == 'foo=bar'
            self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=lbu_name,
                                                           LoadBalancerAttributes={'AdditionalAttributes': [{
                                                               'Key': 'SecuredCookies', 'Value': True}]})
            time.sleep(30)
            ret = requests.get("https://{}/cookie".format(dns_name), verify=False)
            assert ret.headers['Set-Cookie'] == 'foo=bar; Secure'
        except OscApiException as err:
            raise err
        finally:
            if ret_lbu:
                try:
                    delete_lbu(self.a1_r1, lbu_name)
                except:
                    pass
            if ret_up:
                try:
                    self.a1_r1.eim.DeleteServerCertificate(ServerCertificateName=name)
                except:
                    pass
            if crtpath:
                os.remove(crtpath)
            if keypath:
                os.remove(keypath)