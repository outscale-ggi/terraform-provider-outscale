# -*- coding: utf-8 -*-

import re
from datetime import datetime

import time

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import wait
from qa_tina_tools.tina.setup_tools import setup_customer_gateway
from qa_tina_tools.tools.tina import wait_tools
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, ROUTE_TABLE_ID, SECURITY_GROUP_ID, SUBNETS, KEY_PAIR, \
    VPC_ID, PATH, INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_vpn_connections_state


class Test_multi_vpn(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_multi_vpn, cls).setup_class()
        cls.zones = cls.a1_r1.config.region.get_info(constants.ZONE)
        if len(cls.zones) < 2:
            raise OscTestException('Test needs more than one az to be executed')
        cls.inst_cgw1_info = None
        cls.inst_cgw2_info = None
        cls.vpc_info = None
        cls.cgw1_id = None
        cls.cgw2_id = None
        cls.vgw_id = None

    @classmethod
    def teardown_class(cls):
        super(Test_multi_vpn, cls).teardown_class()

    def setup_method(self, method):
        super(Test_multi_vpn, self).setup_method(method)
        self.inst_cgw1_info = None
        self.inst_cgw2_info = None
        self.vpc_info = None
        self.cgw1_id = None
        self.cgw2_id = None
        self.vgw_id = None
        try:
            # create a pub instance for the CGW
            self.inst_cgw1_info = create_instances(osc_sdk=self.a1_r1, az=self.zones[0])
            self.inst_cgw2_info = create_instances(osc_sdk=self.a1_r1, az=self.zones[1])

            # create CGW with pub instance IP
            ret = self.a1_r1.fcu.CreateCustomerGateway(BgpAsn=65000, IpAddress=self.inst_cgw1_info[INSTANCE_SET][0]['ipAddress'], Type='ipsec.1')
            self.cgw1_id = ret.response.customerGateway.customerGatewayId
            # create CGW with private instance IPmbre
            ret = self.a1_r1.fcu.CreateCustomerGateway(BgpAsn=65000, IpAddress=self.inst_cgw2_info[INSTANCE_SET][0]['ipAddress'], Type='ipsec.1')
            self.cgw2_id = ret.response.customerGateway.customerGatewayId

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
            if self.vpc_info:
                delete_vpc(self.a1_r1, self.vpc_info)
            if self.vgw_id:
                self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=self.vgw_id)
                wait_tools.wait_vpn_gateways_state(self.a1_r1, [self.vgw_id], state='deleted')
            if self.cgw1_id:
                self.a1_r1.fcu.DeleteCustomerGateway(CustomerGatewayId=self.cgw1_id)
                wait_tools.wait_customer_gateways_state(self.a1_r1, [self.cgw1_id], state='deleted')
            if self.cgw2_id:
                self.a1_r1.fcu.DeleteCustomerGateway(CustomerGatewayId=self.cgw2_id)
                wait_tools.wait_customer_gateways_state(self.a1_r1, [self.cgw2_id], state='deleted')
            if self.inst_cgw1_info:
                delete_instances(self.a1_r1, self.inst_cgw1_info)
            if self.inst_cgw2_info:
                delete_instances(self.a1_r1, self.inst_cgw2_info)
        finally:
            super(Test_multi_vpn, self).teardown_method(method)

    def exec_test_vpn(self, static, racoon, default_rtb=True):

        # initialize a VPC with 1 subnet, 1 instance and an igw
        self.vpc_info = create_vpc(osc_sdk=self.a1_r1, nb_instance=1, default_rtb=default_rtb)

        self.a1_r1.fcu.AttachVpnGateway(VpcId=self.vpc_info[VPC_ID], VpnGatewayId=self.vgw_id)        

        rtb_id = None
        if default_rtb:
            rtb_id = self.vpc_info[ROUTE_TABLE_ID]
        else:
            rtb_id = self.vpc_info[SUBNETS][0][ROUTE_TABLE_ID]

        # enable route propagation from VGW to VPC route table
        self.a1_r1.fcu.EnableVgwRoutePropagation(GatewayId=self.vgw_id,
                                                 RouteTableId=rtb_id)

        vpn1_id = None
        vpn2_id = None
        try:
            # create VPN connection
            ret = self.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=self.cgw1_id,
                                                     Type='ipsec.1',
                                                     VpnGatewayId=self.vgw_id,
                                                     Options={'StaticRoutesOnly': static})
            vpn1_id = ret.response.vpnConnection.vpnConnectionId
            wait_vpn_connections_state(self.a1_r1, [vpn1_id], state='available')
            vpn_cfg = ret.response.vpnConnection.customerGatewayConfiguration
            match = re.search('<vpn_gateway><tunnel_outside_address><ip_address>(.+?)</ip_address>', vpn_cfg)
            vgw1_ip = match.group(1)
            match = re.search('<pre_shared_key>(.+?)</pre_shared_key>', vpn_cfg)
            psk1_key = match.group(1)
    
            # open flow from VGW to CGW1
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.inst_cgw1_info[SECURITY_GROUP_ID],
                                                         IpProtocol='udp',
                                                         FromPort=500,
                                                         ToPort=500,
                                                         CidrIp=vgw1_ip)
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.inst_cgw1_info[SECURITY_GROUP_ID],
                                                         IpProtocol='udp',
                                                         FromPort=4500,
                                                         ToPort=4500,
                                                         CidrIp=vgw1_ip)

            # open flow from CGW to VPC instances
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.vpc_info[SUBNETS][0][SECURITY_GROUP_ID],
                                                         IpProtocol='icmp',
                                                         FromPort=-1,
                                                         ToPort=-1,
                                                         CidrIp="{}/32".format(self.inst_cgw1_info[INSTANCE_SET][0]['privateIpAddress']))

            # wait CGW state == ready before making configuration
            wait_tools.wait_instances_state(self.a1_r1, [self.inst_cgw1_info[INSTANCE_ID_LIST][0]], state='ready')

            sshclient1 = SshTools.check_connection_paramiko(self.inst_cgw1_info[INSTANCE_SET][0]['ipAddress'], self.inst_cgw1_info[KEY_PAIR][PATH],
                                                            username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

            setup_customer_gateway(self.a1_r1, sshclient1, self.vpc_info[SUBNETS][0][INSTANCE_SET][0]['privateIpAddress'],
                                   self.inst_cgw1_info, vgw1_ip, psk1_key, static, vpn1_id, racoon=racoon)

            # wait vpc instance state == ready before try to make ping
            wait_tools.wait_instances_state(self.a1_r1,
                                 [self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0]],
                                 state='ready')

            inst1 = self.inst_cgw1_info[INSTANCE_SET][0]
            inst_vpc = self.vpc_info[SUBNETS][0][INSTANCE_SET][0]
            self.logger.info("inst1 cgw -> : %s -- %s".format(inst1['ipAddress'], inst1['privateIpAddress']))
            self.logger.info("inst vpc -> : None -- %s".format(inst_vpc['privateIpAddress']))

            # try to make ping from CGW to VPC instance
            out, _, _ = SshTools.exec_command_paramiko(
                sshclient1,
                'ping -I {} -W 1 -c 1 {}'.format(inst1['privateIpAddress'], inst_vpc['privateIpAddress']),
                retry=20,
                timeout=10)
            assert "1 packets transmitted, 1 received, 0% packet loss" in out

            # check vpn connection status
            start = datetime.now()
            while (datetime.now() - start).total_seconds() < 60:
                try:
                    ret = self.a1_r1.fcu.DescribeVpnConnections(VpnConnectionId=[vpn1_id])
                    self.logger.info('state = %s'.format(ret.response.vpnConnectionSet[0].state))
                    self.logger.info('telemetry = %s'.format(ret.response.vpnConnectionSet[0].vgwTelemetry[0].status))
                    assert ret.response.vpnConnectionSet[0].state == 'available'
                    assert ret.response.vpnConnectionSet[0].vgwTelemetry[0].status == 'UP'
                    break
                except Exception:
                    time.sleep(5)
                    pass

            ret = self.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=self.cgw2_id,
                                                     Type='ipsec.1',
                                                     VpnGatewayId=self.vgw_id,
                                                     Options={'StaticRoutesOnly': static})
            vpn2_id = ret.response.vpnConnection.vpnConnectionId
            wait_vpn_connections_state(self.a1_r1, [vpn2_id], state='available')
            vpn_cfg = ret.response.vpnConnection.customerGatewayConfiguration
            match = re.search('<vpn_gateway><tunnel_outside_address><ip_address>(.+?)</ip_address>', vpn_cfg)
            vgw2_ip = match.group(1)
            match = re.search('<pre_shared_key>(.+?)</pre_shared_key>', vpn_cfg)
            psk2_key = match.group(1)

            # open flow from VGW to CGW2
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.inst_cgw2_info[SECURITY_GROUP_ID],
                                                         IpProtocol='udp',
                                                         FromPort=500,
                                                         ToPort=500,
                                                         CidrIp=vgw2_ip)
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.inst_cgw2_info[SECURITY_GROUP_ID],
                                                         IpProtocol='udp',
                                                         FromPort=4500,
                                                         ToPort=4500,
                                                         CidrIp=vgw2_ip)

            # open flow from CGW to VPC instances
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.vpc_info[SUBNETS][0][SECURITY_GROUP_ID],
                                                         IpProtocol='icmp',
                                                         FromPort=-1,
                                                         ToPort=-1,
                                                         CidrIp="{}/32".format(self.inst_cgw2_info[INSTANCE_SET][0]['privateIpAddress']))

            # wait CGW state == ready before making configuration
            wait_tools.wait_instances_state(self.a1_r1, [self.inst_cgw2_info[INSTANCE_ID_LIST][0]], state='ready')

            sshclient2 = SshTools.check_connection_paramiko(self.inst_cgw2_info[INSTANCE_SET][0]['ipAddress'], self.inst_cgw2_info[KEY_PAIR][PATH],
                                                            username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))

            setup_customer_gateway(self.a1_r1, sshclient2, self.vpc_info[SUBNETS][0][INSTANCE_SET][0]['privateIpAddress'],
                                   self.inst_cgw2_info, vgw2_ip, psk2_key, static, vpn2_id, index=1, racoon=racoon)

            inst2 = self.inst_cgw2_info[INSTANCE_SET][0]
            self.logger.info("inst2 cgw -> : %s -- %s".format(inst2['ipAddress'], inst2['privateIpAddress']))
            self.logger.info("inst vpc -> : None -- %s".format(inst_vpc['privateIpAddress']))

            # try to make ping from CGW to VPC instance
            out, _, _ = SshTools.exec_command_paramiko(
                sshclient2,
                'ping -I {} -W 1 -c 1 {}'.format(inst2['privateIpAddress'], inst_vpc['privateIpAddress']),
                retry=20,
                timeout=10)
            assert "1 packets transmitted, 1 received, 0% packet loss" in out

            # check vpn connection status
            start = datetime.now()
            while (datetime.now() - start).total_seconds() < 60:
                try:
                    ret = self.a1_r1.fcu.DescribeVpnConnections(VpnConnectionId=[vpn2_id])
                    self.logger.info('state = %s'.format(ret.response.vpnConnectionSet[0].state))
                    self.logger.info('telemetry = %s'.format(ret.response.vpnConnectionSet[0].vgwTelemetry[0].status))
                    assert ret.response.vpnConnectionSet[0].state == 'available'
                    assert ret.response.vpnConnectionSet[0].vgwTelemetry[0].status == 'UP'
                    break
                except Exception:
                    time.sleep(5)
                    pass

            # try to make ping from CGW to VPC instance
            out, _, _ = SshTools.exec_command_paramiko(
                sshclient1,
                'ping -I {} -W 1 -c 1 {}'.format(inst1['privateIpAddress'], inst_vpc['privateIpAddress']),
                retry=20,
                timeout=10)
            assert "1 packets transmitted, 1 received, 0% packet loss" in out

            # check vpn connection status
            start = datetime.now()
            while (datetime.now() - start).total_seconds() < 60:
                try:
                    ret = self.a1_r1.fcu.DescribeVpnConnections(VpnConnectionId=[vpn1_id])
                    self.logger.info('state = %s'.format(ret.response.vpnConnectionSet[0].state))
                    self.logger.info('telemetry = %s'.format(ret.response.vpnConnectionSet[0].vgwTelemetry[0].status))
                    assert ret.response.vpnConnectionSet[0].state == 'available'
                    assert ret.response.vpnConnectionSet[0].vgwTelemetry[0].status == 'UP'
                    break
                except Exception:
                    time.sleep(5)
                    pass

        finally:
            # delete VPN connection
            if vpn1_id:
                ret = self.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn1_id)
            if vpn2_id:
                ret = self.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn2_id)
            wait.wait_VpnConnections_state(self.a1_r1, [vpn1_id, vpn2_id], state='deleted', cleanup=True)

            self.a1_r1.fcu.DetachVpnGateway(VpcId=self.vpc_info[VPC_ID], VpnGatewayId=self.vgw_id)
            wait_tools.wait_vpn_gateways_attachment_state(self.a1_r1, [self.vgw_id], 'detached')

    def test_T1948_test_vpn_static(self):
        self.exec_test_vpn(static=False, racoon=True, default_rtb=True)

    def test_T5143_test_vpn_static_strongswan(self):
        self.exec_test_vpn(static=False, racoon=False, default_rtb=True)
