import socket

import pytest
import time

from qa_common_tools.ssh import SshTools
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import check_tools
from qa_tina_tools.tina.check_tools import wait_health, dns_test
from qa_tina_tools.tina.setup_tools import start_http_server, install_udp_server
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_load_balancers
from qa_tina_tools.tools.tina.create_tools import create_load_balancer, create_instances, create_vpc, \
    create_security_group
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_vpc, delete_security_group_old, delete_lbu
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, KEY_PAIR, PATH, SECURITY_GROUP_ID, SUBNETS, SUBNET_ID, \
    VPC_ID, INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


class Test_load_balancers(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_load_balancers, cls).setup_class()
        try:
            pass
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_load_balancers, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T1573_public_lbu(self):

        lb_name = id_generator(prefix='lb-')
        ret_lb = None
        ci_info = None
        try:
            ret_lb = create_load_balancer(self.a1_r1, lb_name)
            health_check = {'HealthyThreshold': 2, 'Interval': 20, 'Target': 'HTTP:80/index.html', 'Timeout': 10, 'UnhealthyThreshold': 2}
            self.a1_r1.lbu.ConfigureHealthCheck(LoadBalancerName=lb_name, HealthCheck=health_check)
            ci_info = create_instances(self.a1_r1, 2, state='ready')
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=ci_info[SECURITY_GROUP_ID], IpProtocol='tcp',
                                                         FromPort=80, ToPort=80, CidrIp=Configuration.get('cidr', 'allips'))
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=ci_info[SECURITY_GROUP_ID], IpProtocol='tcp',
                                                         FromPort=443, ToPort=443, CidrIp=Configuration.get('cidr', 'allips'))
            insts = []
            for inst in ci_info[INSTANCE_SET]:
                start_http_server(inst['ipAddress'], ci_info[KEY_PAIR][PATH], self.a1_r1.config.region.get_info(constants.CENTOS_USER),
                                  text='ins{}'.format(inst['instanceId']))

                insts.append({'InstanceId': inst['instanceId']})
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=lb_name, Instances=insts)
            wait_health(self.a1_r1, lb_name, insts, 'InService')
            dns_test(self.a1_r1, ret_lb.response.CreateLoadBalancerResult.DNSName)
            self.a1_r1.lbu.CreateLBCookieStickinessPolicy(LoadBalancerName=lb_name, PolicyName='policyname', CookieExpirationPeriod=1)
            self.a1_r1.lbu.SetLoadBalancerPoliciesOfListener(LoadBalancerName=lb_name, LoadBalancerPort=80, PolicyNames=['policyname'])
            wait_health(self.a1_r1, lb_name, insts, 'InService')
            dns_test(self.a1_r1, ret_lb.response.CreateLoadBalancerResult.DNSName, withsession=True, check_cookies=True)
            # for debug purposes
        except Exception as error:
            self.logger.exception(str(error))
            raise error
        finally:
            if ci_info:
                delete_instances(self.a1_r1, ci_info)
            if ret_lb:
                delete_lbu(self.a1_r1, lbu_name=lb_name)

    @pytest.mark.tag_redwire
    def test_T1574_private_internal_lbu(self):
        lb_name = id_generator(prefix='lb-')
        ret_lb = None
        vpc_info = None
        eips = []
        try:
            vpc_info = create_vpc(self.a1_r1, nb_instance=3, state='ready', no_eip=True)
            vpc_subnet = vpc_info[SUBNETS][0]
            vpc_insts = vpc_subnet[INSTANCE_SET]
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=vpc_subnet[SECURITY_GROUP_ID], IpProtocol='tcp',
                                                         FromPort=80, ToPort=80, CidrIp=Configuration.get('cidr', 'allips'))
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=vpc_subnet[SECURITY_GROUP_ID], IpProtocol='tcp',
                                                         FromPort=443, ToPort=443, CidrIp=Configuration.get('cidr', 'allips'))
            ret_lb = create_load_balancer(self.a1_r1, lb_name, subnets=[vpc_subnet[SUBNET_ID]], scheme='internal').response.CreateLoadBalancerResult
            health_check = {'HealthyThreshold': 2, 'Interval': 20, 'Target': 'HTTP:80/index.html', 'Timeout': 10, 'UnhealthyThreshold': 2}
            self.a1_r1.lbu.ConfigureHealthCheck(LoadBalancerName=lb_name, HealthCheck=health_check)
            for i in range(3):
                eips.append(self.a1_r1.fcu.AllocateAddress(Domain='vpc').response)
                self.a1_r1.fcu.AssociateAddress(InstanceId=vpc_insts[i]['instanceId'], AllocationId=eips[i].allocationId)
            insts = []
            for i in range(2):
                inst = vpc_insts[i]
                start_http_server(eips[i].publicIp, vpc_info[KEY_PAIR][PATH], self.a1_r1.config.region.get_info(constants.CENTOS_USER))
                insts.append({'InstanceId': inst['instanceId']})
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=lb_name, Instances=insts)
            wait_health(self.a1_r1, lb_name, insts, 'InService')
            # yum install wget
            # run command on instance wget -o /tmp/toto.txt http://....
            # check output file for http response status (regex)
            sshclient = check_tools.check_ssh_connection(self.a1_r1, vpc_insts[2], eips[2].publicIp, vpc_info[KEY_PAIR][PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # sshclient = SshTools.check_connection_paramiko(eips[2].publicIp, vpc_info[KEY_PAIR][PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            SshTools.exec_command_paramiko(sshclient, "sudo yum install -y bind-utils", eof_time_out=300)
            SshTools.exec_command_paramiko(sshclient, "nslookup {}".format(ret_lb.DNSName), retry=6, timeout=10)
            SshTools.exec_command_paramiko(sshclient, "sudo curl -v -o /tmp/out.html {} &> /tmp/out.log".format(ret_lb.DNSName))
            SshTools.exec_command_paramiko(sshclient, "sudo grep '< HTTP/1.* 200 OK' /tmp/out.log")

            # for debug purposes
        except Exception as error:
            self.logger.exception(str(error))
            raise error
        finally:
            if ret_lb:
                delete_lbu(self.a1_r1, lbu_name=lb_name)
            if vpc_info:
                delete_vpc(self.a1_r1, vpc_info)
            if eips:
                for eip in eips:
                    self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)

    @pytest.mark.tag_redwire
    def test_T1575_private_internet_lbu(self):
        lb_name = id_generator(prefix='lb-')
        ret_lb = None
        lb_sg = None
        vpc_info = None
        eips = []
        try:
            vpc_info = create_vpc(self.a1_r1, nb_instance=2, state='ready', no_eip=True)
            vpc_subnet = vpc_info[SUBNETS][0]
            vpc_insts = vpc_subnet[INSTANCE_SET]
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=vpc_subnet[SECURITY_GROUP_ID], IpProtocol='tcp',
                                                         FromPort=80, ToPort=80, CidrIp=Configuration.get('cidr', 'allips'))
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=vpc_subnet[SECURITY_GROUP_ID], IpProtocol='tcp',
                                                         FromPort=443, ToPort=443, CidrIp=Configuration.get('cidr', 'allips'))
            lb_sg = create_security_group(self.a1_r1, vpc_id=vpc_info[VPC_ID])
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=lb_sg, IpProtocol='tcp',
                                                         FromPort=80, ToPort=80, CidrIp=Configuration.get('cidr', 'allips'))
            ret_lb = create_load_balancer(self.a1_r1, lb_name, subnets=[vpc_subnet[SUBNET_ID]],
                                          scheme='internet-facing', sg=[lb_sg]).response.CreateLoadBalancerResult
            health_check = {'HealthyThreshold': 2, 'Interval': 20, 'Target': 'HTTP:80/index.html', 'Timeout': 10, 'UnhealthyThreshold': 2}
            self.a1_r1.lbu.ConfigureHealthCheck(LoadBalancerName=lb_name, HealthCheck=health_check)
            for i in range(2):
                eips.append(self.a1_r1.fcu.AllocateAddress(Domain='vpc').response)
                self.a1_r1.fcu.AssociateAddress(InstanceId=vpc_insts[i]['instanceId'], AllocationId=eips[i].allocationId)
            insts = []
            for i in range(2):
                inst = vpc_insts[i]
                start_http_server(eips[i].publicIp, vpc_info[KEY_PAIR][PATH], self.a1_r1.config.region.get_info(constants.CENTOS_USER))
                insts.append({'InstanceId': inst['instanceId']})
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=lb_name, Instances=insts)
            wait_health(self.a1_r1, lb_name, insts, 'InService')
            dns_test(self.a1_r1, ret_lb.DNSName)

            # for debug purposes
        except Exception as error:
            self.logger.exception(str(error))
            raise error
        finally:
            if ret_lb:
                cleanup_load_balancers(self.a1_r1, load_balancer_name_list=[lb_name])
            if lb_sg:
                delete_security_group_old(self.a1_r1, sg_id=lb_sg)
            if vpc_info:
                delete_vpc(self.a1_r1, vpc_info)
            if eips:
                for eip in eips:
                    self.a1_r1.fcu.ReleaseAddress(PublicIp=eip.publicIp)

    def test_T4657_lbu_with_udp(self):
        inst_info = None
        try:
            inst_info = create_instances(self.a1_r1, state='running')
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=inst_info[SECURITY_GROUP_ID], IpProtocol='tcp',
                                                         FromPort=80, ToPort=80, CidrIp=Configuration.get('cidr', 'allips'))
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=inst_info[SECURITY_GROUP_ID], IpProtocol='udp',
                                                         FromPort=12000, ToPort=12000, CidrIp=Configuration.get('cidr', 'allips'))
            wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=inst_info[INSTANCE_ID_LIST], state='ready')
            install_udp_server(inst_info[INSTANCE_SET][0]['ipAddress'], inst_info[KEY_PAIR][PATH], self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            for pings in range(10):
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                client_socket.settimeout(1.0)
                message = b'test'
                addr = ("{}".format(inst_info[INSTANCE_SET][0]['ipAddress']), 12000)
            
                start = time.time()
                client_socket.sendto(message, addr)
                try:
                    data, _ = client_socket.recvfrom(1024)
                    end = time.time()
                    elapsed = end - start
                    print('{} {} {}'.format(data, pings, elapsed))
                    if data:
                        break
                except socket.timeout:
                    print('REQUEST TIMED OUT')
                time.sleep(1)
        except OscApiException as err:
            raise err
        finally:
            delete_instances(self.a1_r1, inst_info)

    def test_T5056_public_lbu_with_AppCookieStickinessPolicy(self):

        lb_name = id_generator(prefix='lb-')
        ret_lb = None
        ci_info = None
        try:
            ret_lb = create_load_balancer(self.a1_r1, lb_name)
            dns_name = ret_lb.response.CreateLoadBalancerResult.DNSName
            health_check = {'HealthyThreshold': 2, 'Interval': 20, 'Target': 'HTTP:80/index.html', 'Timeout': 10, 'UnhealthyThreshold': 2}
            self.a1_r1.lbu.ConfigureHealthCheck(LoadBalancerName=lb_name, HealthCheck=health_check)
            ci_info = create_instances(self.a1_r1, 2, state='ready')
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=ci_info[SECURITY_GROUP_ID], IpProtocol='tcp',
                                                         FromPort=80, ToPort=80, CidrIp=Configuration.get('cidr', 'allips'))
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=ci_info[SECURITY_GROUP_ID], IpProtocol='tcp',
                                                         FromPort=443, ToPort=443, CidrIp=Configuration.get('cidr', 'allips'))
            insts = ci_info[INSTANCE_SET][0]
            start_http_server(insts['ipAddress'], ci_info[KEY_PAIR][PATH], self.a1_r1.config.region.get_info(constants.CENTOS_USER),
                              text='ins{}'.format(insts['instanceId']))
            insts=[{'InstanceId': insts['instanceId']}]
            self.a1_r1.lbu.RegisterInstancesWithLoadBalancer(LoadBalancerName=lb_name, Instances=insts)
            wait_health(self.a1_r1, lb_name, insts, 'InService')
            dns_test(self.a1_r1, ret_lb.response.CreateLoadBalancerResult.DNSName)            
            self.a1_r1.lbu.CreateAppCookieStickinessPolicy(LoadBalancerName=lb_name, PolicyName='my-app-cookie-policy', CookieName=lb_name)
            self.a1_r1.lbu.SetLoadBalancerPoliciesOfListener(LoadBalancerName=lb_name , LoadBalancerPort = 80, PolicyNames=['my-app-cookie-policy'])
            wait_health(self.a1_r1, lb_name, insts, 'InService')
            dns_test(self.a1_r1, dns_name=ret_lb.response.CreateLoadBalancerResult.DNSName)
        except Exception as error:
            self.logger.exception(str(error))
            raise error
        finally:
            if ci_info:
                delete_instances(self.a1_r1, ci_info)
            if ret_lb:
                delete_lbu(self.a1_r1, lbu_name=lb_name)
