import random
import time

from netaddr import IPNetwork, IPAddress
import pytest

from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import wait
from qa_tina_tools.tools.tina import wait_tools
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, delete_lbu
from qa_tina_tools.tools.tina.info_keys import VPC_ID


@pytest.mark.region_admin
class Test_get_ssh_infos(OscTinaTest):

    def test_T5863_for_vgw(self):
        cgw_id = None
        vgw_id = None
        vpn_id = None
        try:
            ret = self.a1_r1.fcu.CreateCustomerGateway(BgpAsn=65000,
                                                       IpAddress='.'.join(str(i) for i in random.sample(list(range(1, 254)), 4)),
                                                       Type='ipsec.1')
            cgw_id = ret.response.customerGateway.customerGatewayId

            ret = self.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1')
            vgw_id = ret.response.vpnGateway.vpnGatewayId

            ret = self.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=cgw_id,
                                                     Type='ipsec.1',
                                                     VpnGatewayId=vgw_id,
                                                     Options={'StaticRoutesOnly': True})
            vpn_id = ret.response.vpnConnection.vpnConnectionId
            wait_tools.wait_vpn_connections_state(self.a1_r1, [vpn_id], state='available')

            ret = self.a1_r1.intel.netimpl.firewall.get_firewalls(resource=vgw_id)
            inst_id = ret.response.result.master.vm
            wait_tools.wait_instance_service_state(self.a1_r1, [inst_id], state='ready')
            ret = self.a1_r1.intel.nic.find(filters={'vm': inst_id})
            inst_ip = None
            for nic in ret.response.result:
                if IPAddress(nic.ips[0].ip) in IPNetwork(self.a1_r1.config.region.get_info(constants.FW_ADMIN_SUBNET)):
                    inst_ip = nic.ips[0].ip
            assert inst_ip
            try:
                ret = self.a1_r1.intel.netimpl.firewall.get_ssh_infos(resource=inst_id)
                assert ret.response.result != 'ssh root@' + inst_ip
                known_error('TINA-6688', 'get_ssh_infos does not work as expected')
            except AssertionError:
                assert False, 'Remove known error and adapt the assertion'
        finally:
            if vpn_id:
                self.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn_id)
                wait.wait_VpnConnections_state(self.a1_r1, [vpn_id], state='deleted', cleanup=True)
            if vgw_id:
                self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=vgw_id)
                wait_tools.wait_vpn_gateways_state(self.a1_r1, [vgw_id], state='deleted')
            if cgw_id:
                self.a1_r1.fcu.DeleteCustomerGateway(CustomerGatewayId=cgw_id)
                wait_tools.wait_customer_gateways_state(self.a1_r1, [cgw_id], state='deleted')

    def test_T5864_for_vpc(self):
        vpc_info = None
        try:
            vpc_info = create_vpc(self.a1_r1, nb_instance=1, igw=True)

            ret = self.a1_r1.intel.netimpl.firewall.get_firewalls(resource=vpc_info[VPC_ID])
            inst_id = ret.response.result.master.vm

            ret = self.a1_r1.intel.nic.find(filters={'vm': inst_id})

            inst_ip = None
            for nic in ret.response.result:
                if IPAddress(nic.ips[0].ip) in IPNetwork(self.a1_r1.config.region.get_info(constants.FW_ADMIN_SUBNET)):
                    inst_ip = nic.ips[0].ip
            assert inst_ip
            try:
                ret = self.a1_r1.intel.netimpl.firewall.get_ssh_infos(resource=inst_id)
                assert ret.response.result != 'ssh root@' + inst_ip
                known_error('TINA-6688', 'get_ssh_infos does not work as expected')
            except AssertionError:
                assert False, 'Remove known error and adapt the assertion'
        finally:
            if vpc_info:
                delete_vpc(self.a1_r1, vpc_info)

    def test_t5865_for_lbu(self):
        try:
            lb_name = None
            lbu_name = id_generator('lbu')
            self.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                              LoadBalancerName=lbu_name,
                                              AvailabilityZones=[self.a1_r1.config.region.az_name])

            time.sleep(10)
            lb_name = lbu_name
            ret = self.a1_r1.intel_lbu.lb.get(owner=self.a1_r1.config.account.account_id,
                                              names=[lb_name])

            inst_id = ret.response.result[0].lbu_instance
            ret = self.a1_r1.intel.nic.find(filters={'vm': inst_id})
            inst_ip = None
            for nic in ret.response.result:
                if IPAddress(nic.ips[0].ip) in IPNetwork(self.a1_r1.config.region.get_info(constants.FW_ADMIN_SUBNET)):
                    inst_ip = nic.ips[0].ip
            assert inst_ip
            try:
                ret = self.a1_r1.intel.netimpl.firewall.get_ssh_infos(resource=inst_id)
                assert ret.response.result != 'ssh root@' + inst_ip
                known_error('TINA-6688', 'get_ssh_infos does not work as expected')
            except AssertionError:
                assert False, 'Remove known error and adapt the assertion'
        finally:
            if lb_name:
                delete_lbu(self.a1_r1, lbu_name=lb_name)
