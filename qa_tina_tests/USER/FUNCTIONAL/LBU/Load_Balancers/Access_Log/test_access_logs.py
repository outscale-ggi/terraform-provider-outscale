from string import ascii_lowercase

import time
import requests

from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tina.setup_tools import start_http_server
from qa_tina_tools.tools.tina.create_tools import create_load_balancer, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_lbu
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, INSTANCE_SET, PATH, KEY_PAIR, SECURITY_GROUP_ID
from qa_tina_tools.tina.check_tools import wait_lbu_backend_state


class Test_access_logs(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.lb_name = id_generator(prefix='lbu-')
        cls.lbu_resp = None
        cls.inst_info = None
        cls.ret_reg = None
        cls.inst_id_list = []
        super(Test_access_logs, cls).setup_class()
        try:
            cls.lbu_resp = create_load_balancer(cls.a1_r1, cls.lb_name, listeners=[{'InstancePort': 80,
                                                                                    'InstanceProtocol': 'HTTP',
                                                                                    'Protocol': 'HTTP',
                                                                                    'LoadBalancerPort': 80}],
                                                availability_zones=[cls.a1_r1.config.region.az_name])
            cls.inst_info = create_instances(cls.a1_r1)
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=cls.inst_info[SECURITY_GROUP_ID],
                                                        IpProtocol='tcp',
                                                        FromPort=80, ToPort=80,
                                                        CidrIp=Configuration.get('cidr', 'allips'))
            kp_info = cls.inst_info[KEY_PAIR]
            start_http_server(cls.inst_info[INSTANCE_SET][0]['ipAddress'], kp_info[PATH],
                                  cls.a1_r1.config.region.get_info(constants.CENTOS_USER), text=cls.inst_info[INSTANCE_ID_LIST][0])
            cls.ret_reg = cls.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=cls.lb_name, Instances=[{'InstanceId': cls.inst_info[INSTANCE_ID_LIST][0]}])
            wait_lbu_backend_state(cls.a1_r1, cls.lb_name)
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret_reg:
                cls.a1_r1.lbu.DeregisterInstancesFromLoadBalancer(LoadBalancerName=cls.lb_name, Instances=[{'InstanceId': cls.inst_info[INSTANCE_ID_LIST][0]}])
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
            if cls.lbu_resp:
                delete_lbu(cls.a1_r1, lbu_name=cls.lb_name)
        finally:
            super(Test_access_logs, cls).teardown_class()

    def test_T5535_lbu_access_logs(self):
        ret_create_bucket = None
        bucket_name = id_generator(prefix="bucket", chars=ascii_lowercase)
        try:
            ret_create_bucket = self.a1_r1.storageservice.create_bucket(Bucket=bucket_name)

            access_log = {'S3BucketName': bucket_name, 'S3BucketPrefix': 'prefix', 'EmitInterval': 5, 'Enabled': True}
            self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerAttributes={'AccessLog': access_log},
                                                        LoadBalancerName=self.lb_name)
            for _ in range(10):
                requests.get("http://{}".format(self.lbu_resp.response.CreateLoadBalancerResult.DNSName), verify=False)
                time.sleep(10)

        finally:
            try:
                ret = self.a1_r1.oos.list_objects(Bucket=bucket_name)
                if len(ret['Contents']) == 1:
                    known_error('TINA-6008', 'No logs in bucket for lbu access log')
                else:
                    assert False, 'Remove known error'
            finally:
                if 'Contents' in list(ret.keys()):
                    for j in ret['Contents']:
                        self.a1_r1.oos.delete_object(Bucket=bucket_name, Key=j['Key'])
                if ret_create_bucket:
                    self.a1_r1.storageservice.delete_bucket(Bucket=bucket_name)