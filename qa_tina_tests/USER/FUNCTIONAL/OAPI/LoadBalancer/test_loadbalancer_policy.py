import time

import requests

from qa_test_tools import misc
from qa_test_tools.config import config_constants as constants
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import oapi, wait, info_keys, setup_tools


class Test_loadbalancer_policy(OscTestSuite):

    @classmethod
    def setup_class(cls, ):
        super(Test_loadbalancer_policy, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_loadbalancer_policy, cls).teardown_class()

    def test_T5343_lbu_policy(self):
        try:
            vm_info = oapi.create_Vms(self.a1_r1, vm_type=self.a1_r1.config.region.get_info(constants.DEFAULT_GPU_INSTANCE_TYPE))
            vm_lb_policy_info = oapi.create_Vms(self.a1_r1, vm_type=self.a1_r1.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE))
            wait.wait_Vms_state(self.a1_r1, [vm_info[info_keys.VM_IDS][0],
                                             vm_lb_policy_info[info_keys.VM_IDS][0]], state='ready')
            kp_path = vm_info[info_keys.KEY_PAIR][info_keys.PATH]
            lbu_info = oapi.create_LoadBalancer(self.a1_r1, misc.id_generator(prefix='lb-'))
            self.a1_r1.oapi.CreateSecurityGroupRule(SecurityGroupId=vm_info[info_keys.SECURITY_GROUP_ID],
                                                    Rules=[{'SecurityGroupsMembers': [{"AccountId": "outscale-elb",
                                                                                       "SecurityGroupName": "outscale-elb-sg"}]}],
                                                    Flow='Inbound')

            self.a1_r1.oapi.CreateSecurityGroupRule(SecurityGroupId=vm_lb_policy_info[info_keys.SECURITY_GROUP_ID],
                                                    Rules=[{'SecurityGroupsMembers': [{"AccountId": "outscale-elb",
                                                                                       "SecurityGroupName":
                                                                                       "outscale-elb-sg"}]}],
                                                    Flow='Inbound')

            vm_ip = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [vm_info[info_keys.VM_IDS][0]]}).response.Vms[0].PublicIp
            loadbalancer_policy_vm_ip = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [vm_lb_policy_info[info_keys.VM_IDS][0]]}).response.Vms[0].PublicIp
            setup_tools.start_http_server(vm_ip, kp_path,
                                          self.a1_r1.config.region.get_info(constants.CENTOS_USER), "back_1")
            setup_tools.start_http_server(loadbalancer_policy_vm_ip,
                                          vm_lb_policy_info[info_keys.KEY_PAIR][info_keys.PATH],
                                          self.a1_r1.config.region.get_info(constants.CENTOS_USER), "back_2")
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=lbu_info[info_keys.LBU_NAME],
                                                      BackendVmIds=[vm_info[info_keys.VM_IDS][0],
                                                                    vm_lb_policy_info[info_keys.VM_IDS][0]])
            request_passed = False
            wait.wait_LoadBalancer_Backends_state(self.a1_r1, lbu_info[info_keys.LBU_NAME])
            for _ in range(5):
                response = requests.get("http://{}".format(lbu_info[info_keys.LBU_DNS]))
                if response.status_code == 200:
                    request_passed = True
                    break
                time.sleep(2)
            assert request_passed, 'request failed'
            cookie_found = False
            policy_name = misc.id_generator(prefix='policy-')
            self.a1_r1.oapi.CreateLoadBalancerPolicy(LoadBalancerName=lbu_info[info_keys.LBU_NAME],
                                                     PolicyName=policy_name, PolicyType='load_balancer')
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=lbu_info[info_keys.LBU_NAME], PolicyNames=[policy_name],
                                               LoadBalancerPort=80)
            session = requests.session()
            for _ in range(5):
                response = session.get("http://{}".format(lbu_info[info_keys.LBU_DNS]))
                if response.status_code == 200 and len(getattr(response.cookies, '_cookies')) >= 1:
                    cookie_found = True
                    break
                time.sleep(2)
            assert cookie_found, 'cookie not found'
            text = response.text
            for _ in range(2):
                response = session.get("http://{}".format(lbu_info[info_keys.LBU_DNS]))
                assert response.status_code == 200
                assert response.text == text
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=lbu_info[info_keys.LBU_NAME], PolicyNames=[],
                                               LoadBalancerPort=80)

            time.sleep(30)
            cookie_found = False
            session = requests.session()
            for _ in range(5):
                response = session.get("http://{}".format(lbu_info[info_keys.LBU_DNS]))
                if response.status_code == 200 and len(getattr(response.cookies, '_cookies')) >= 1:
                    if len(getattr(response.cookies, '_cookies')) >= 1:
                        cookie_found = True
                        assert False, 'cookie found after its deletion '
                    else:
                        break
                time.sleep(2)
            assert not cookie_found, 'cookie found'
            text = response.text
            for _ in range(2):
                response = session.get("http://{}".format(lbu_info[info_keys.LBU_DNS]))
                assert response.status_code == 200
                assert response.text != text
                text = response.text
        finally:
            errors =[]
            if vm_info:
                try:
                    oapi.delete_Vms(self.a1_r1, vm_info)
                except Exception as error:
                    errors.append(error)
            if vm_lb_policy_info:
                try:
                    oapi.delete_Vms(self.a1_r1, vm_lb_policy_info)
                except Exception as error:
                    errors.append(error)
            if lbu_info:
                try:
                    oapi.delete_LoadBalancer(self.a1_r1, lbu_info)
                except Exception as error:
                    errors.append(error)
            if errors:
                raise OscTestException('Found {} errors while cleaning resources : \n{}'.format(len(errors), errors))
