# -*- coding: utf-8 -*-

from datetime import datetime
import re
import time

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, ROUTE_TABLE_ID, SECURITY_GROUP_ID, SUBNETS, KEY_PAIR, VPC_ID, PATH, INSTANCE_ID_LIST
from qa_common_tools.ssh import SshTools, OscCommandError
from qa_tina_tools.tools.tina.wait_tools import wait_customer_gateways_state, wait_vpn_gateways_attachment_state
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_tina_tools.tools.tina.wait_tools import wait_vpn_connections_state
from qa_tina_tools.tools.tina.wait_tools import wait_vpn_gateways_state
from qa_tina_tools.tina.setup_tools import setup_customer_gateway
from qa_test_tools.config import config_constants as constants


class Vpn(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Vpn, cls).setup_class()
        cls.inst_cgw_info = None
        cls.vpc_info = None
        cls.cgw_id = None
        cls.vgw_id = None

    @classmethod
    def teardown_class(cls):
        super(Vpn, cls).teardown_class()

    def setup_method(self, method):
        super(Vpn, self).setup_method(method)
        self.inst_cgw_info = None
        self.vpc_info = None
        self.cgw_id = None
        self.vgw_id = None
        try:
            # create a pub instance for the CGW
            self.inst_cgw_info = create_instances(osc_sdk=self.a1_r1)

            # create CGW with pub instance IP
            ret = self.a1_r1.fcu.CreateCustomerGateway(BgpAsn=65000, IpAddress=self.inst_cgw_info[INSTANCE_SET][0]['ipAddress'], Type='ipsec.1')
            self.cgw_id = ret.response.customerGateway.customerGatewayId

            # create and attach VGW
            ret = self.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1')
            self.vgw_id = ret.response.vpnGateway.vpnGatewayId
        except Exception as error:
            try:
                self.teardown_method(method)
            finally:
                raise error

    def teardown_method(self, method):
        try:
            # delete all created ressources in setup
            if self.vgw_id:
                self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=self.vgw_id)
                wait_vpn_gateways_state(self.a1_r1, [self.vgw_id], state='deleted')
            if self.cgw_id:
                self.a1_r1.fcu.DeleteCustomerGateway(CustomerGatewayId=self.cgw_id)
                wait_customer_gateways_state(self.a1_r1, [self.cgw_id], state='deleted')
            if self.vpc_info:
                delete_vpc(self.a1_r1, self.vpc_info)
            if self.inst_cgw_info:
                delete_instances(self.a1_r1, self.inst_cgw_info)
        finally:
            super(Vpn, self).teardown_method(method)

    def exec_test_vpn(self, static, default_rtb=True):

        # initialize a VPC with 1 subnet, 1 instance and an igw
        self.vpc_info = create_vpc(osc_sdk=self.a1_r1, nb_instance=1, default_rtb=default_rtb)

        self.a1_r1.fcu.AttachVpnGateway(VpcId=self.vpc_info[VPC_ID], VpnGatewayId=self.vgw_id)

        # create VPN connection
        ret = self.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=self.cgw_id,
                                                 Type='ipsec.1',
                                                 VpnGatewayId=self.vgw_id,
                                                 Options={'StaticRoutesOnly': static})
        vpn_id = ret.response.vpnConnection.vpnConnectionId
        vpn_cfg = ret.response.vpnConnection.customerGatewayConfiguration
        match = re.search('<vpn_gateway><tunnel_outside_address><ip_address>(.+?)</ip_address>', vpn_cfg)
        vgw_ip = match.group(1)
        match = re.search('<pre_shared_key>(.+?)</pre_shared_key>', vpn_cfg)
        psk_key = match.group(1)

        try:
            # open flow from VGW to CGW
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.inst_cgw_info[SECURITY_GROUP_ID],
                                                         IpProtocol='udp',
                                                         FromPort=500,
                                                         ToPort=500,
                                                         CidrIp=vgw_ip)
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.inst_cgw_info[SECURITY_GROUP_ID],
                                                         IpProtocol='udp',
                                                         FromPort=4500,
                                                         ToPort=4500,
                                                         CidrIp=vgw_ip)

            # open flow from CGW to VPC instances
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.vpc_info[SUBNETS][0][SECURITY_GROUP_ID],
                                                         IpProtocol='icmp',
                                                         FromPort=-1,
                                                         ToPort=-1,
                                                         CidrIp=".".join(
                                                             self.inst_cgw_info[INSTANCE_SET][0]['privateIpAddress'].split('.')[:-1]) + '.0/24')

            rtb_id = None
            if default_rtb:
                rtb_id = self.vpc_info[ROUTE_TABLE_ID]
            else:
                rtb_id = self.vpc_info[SUBNETS][0][ROUTE_TABLE_ID]

            # enable route propagation from VGW to VPC route table
            self.a1_r1.fcu.EnableVgwRoutePropagation(GatewayId=self.vgw_id,
                                                     RouteTableId=rtb_id)

            # wait CGW state == ready before making configuration
            wait_instances_state(self.a1_r1, [self.inst_cgw_info[INSTANCE_ID_LIST][0]], state='ready')

            sshclient = SshTools.check_connection_paramiko(self.inst_cgw_info[INSTANCE_SET][0]['ipAddress'], self.inst_cgw_info[KEY_PAIR][PATH],
                                                           username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

            setup_customer_gateway(self.a1_r1, sshclient, self.vpc_info[SUBNETS][0][INSTANCE_SET][0]['privateIpAddress'],
                                   self.inst_cgw_info, vgw_ip, psk_key, static, vpn_id)

            # wait vpc instance state == ready before try to make ping
            wait_instances_state(self.a1_r1,
                                 [self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0]],
                                 state='ready')

            inst1 = self.inst_cgw_info[INSTANCE_SET][0]
            inst2 = self.vpc_info[SUBNETS][0][INSTANCE_SET][0]
            self.logger.info("inst cgw -> : {} -- {}".format(inst1['ipAddress'], inst1['privateIpAddress']))
            self.logger.info("inst vpc -> : None -- {}".format(inst2['privateIpAddress']))

            # try to make ping from CGW to VPC instance
            try:
                out, _, _ = SshTools.exec_command_paramiko_2(
                    sshclient,
                    'ping -I {} -W 1 -c 1 {}'.format(
                        self.inst_cgw_info[INSTANCE_SET][0]['privateIpAddress'],
                        self.vpc_info[SUBNETS][0][INSTANCE_SET][0]['privateIpAddress']),
                    retry=20,
                    timeout=10)
                assert "1 packets transmitted, 1 received, 0% packet loss" in out
            except OscCommandError:
                raise

            # check vpn connection status
            start = datetime.now()
            while (datetime.now() - start).total_seconds() < 60:
                try:
                    ret = self.a1_r1.fcu.DescribeVpnConnections(VpnConnectionId=[vpn_id])
                    self.logger.info('state = {}'.format(ret.response.vpnConnectionSet[0].state))
                    self.logger.info('telemetry = {}'.format(ret.response.vpnConnectionSet[0].vgwTelemetry[0].status))
                    assert ret.response.vpnConnectionSet[0].state == 'available'
                    assert ret.response.vpnConnectionSet[0].vgwTelemetry[0].status == 'UP'
                    break
                except Exception:
                    time.sleep(5)
                    pass

        finally:
            # delete VPN connection
            ret = self.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn_id)
            wait_vpn_connections_state(self.a1_r1, [vpn_id], state='deleted')

            self.a1_r1.fcu.DetachVpnGateway(VpcId=self.vpc_info[VPC_ID], VpnGatewayId=self.vgw_id)
            wait_vpn_gateways_attachment_state(self.a1_r1, [self.vgw_id], 'detached')
