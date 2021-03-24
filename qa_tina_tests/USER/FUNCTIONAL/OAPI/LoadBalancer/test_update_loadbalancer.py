
import time

from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import id_generator
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.config import config_constants
from qa_tina_tools.tina import oapi, info_keys, setup_tools, check_tools
import time
import pytest


class Test_update_loadbalancer(OscTestSuite):

    def test_update_lbu_sg(self):
        lb_name = id_generator(prefix='lb-')
        lb_info = None
        lb_sg_id = None
        net_info = None
        eips = []
        try:

            net_info = oapi.create_Net(self.a1_r1, nb_vm=2, state='ready', no_eip=True)
            vpc_subnet = net_info[info_keys.SUBNETS][0]
            net_vm_ids = vpc_subnet[info_keys.VM_IDS]

            self.a1_r1.oapi.CreateSecurityGroupRule(Flow='Inbound', SecurityGroupId=vpc_subnet[info_keys.SECURITY_GROUP_ID], IpProtocol='tcp',
                                                         FromPortRange=80, ToPortRange=80, IpRange=Configuration.get('cidr', 'allips'))
            self.a1_r1.oapi.CreateSecurityGroupRule(Flow='Inbound', SecurityGroupId=vpc_subnet[info_keys.SECURITY_GROUP_ID], IpProtocol='tcp',
                                                         FromPortRange=443, ToPortRange=443, IpRange=Configuration.get('cidr', 'allips'))
            lb_info = oapi.create_LoadBalancer(self.a1_r1, lb_name, subnets=[vpc_subnet[info_keys.SUBNET_ID]], lbu_type='internet-facing')
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=lb_name,
                                                     HealthCheck={
                                                         'CheckInterval': 20,
                                                         'HealthyThreshold': 2,
                                                         'Port': 80,
                                                         'Protocol': 'TCP',
                                                         'Timeout': 10,
                                                         'UnhealthyThreshold': 2,
                                                     })
            for vm_id in net_vm_ids:
                eip = self.a1_r1.oapi.CreatePublicIp().response.PublicIp
                eips.append(eip)
                self.a1_r1.oapi.LinkPublicIp(VmId=vm_id, PublicIpId=eip.PublicIpId)
            for eip in eips:
                setup_tools.start_http_server(eip.PublicIp, net_info[info_keys.KEY_PAIR][info_keys.PATH],
                                  self.a1_r1.config.region.get_info(config_constants.CENTOS_USER))
            self.a1_r1.oapi.RegisterVmsInLoadBalancer(LoadBalancerName=lb_name, BackendVmIds=net_vm_ids)
            check_tools.check_health(self.a1_r1, lb_name, net_vm_ids, 'UP', threshold=60)
            try:
                check_tools.dns_test(self.a1_r1, lb_info[info_keys.LBU_DNS], threshold=1)
                pytest.fail('This should not be successful')
            except AssertionError:
                print("Could not connect as expected")

            lb_sg_id = oapi.create_SecurityGroup(self.a1_r1, net_id=net_info[info_keys.NET_ID])
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=lb_sg_id, IpProtocol='tcp',
                                                         FromPort=80, ToPort=80, CidrIp=Configuration.get('cidr', 'allips'))
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=lb_sg_id, IpProtocol='tcp',
                                                         FromPort=443, ToPort=443, CidrIp=Configuration.get('cidr', 'allips'))
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=lb_name, SecurityGroups=[lb_sg_id])

            check_tools.dns_test(self.a1_r1, lb_info[info_keys.LBU_DNS])

            # for debug purposes
        except Exception as error:
            self.logger.exception(str(error))
            raise error
        finally:
            if lb_info:
                oapi.delete_LoadBalancer(self.a1_r1, lb_info)
            if lb_sg_id:
                oapi.delete_SecurityGroup(self.a1_r1, lb_sg_id)
            if net_info:
                oapi.delete_Net(self.a1_r1, net_info)
            for eip in eips:
                self.a1_r1.oapi.DeletePublicIp(PublicIpId=eip.PublicIpId)
