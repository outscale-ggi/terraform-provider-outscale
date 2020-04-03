# -*- coding: utf-8 -*-
'''
Created on 8 aout 2017

@author: EmanuelDias
'''
import datetime
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_customer_gateway
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state, wait_volumes_state, wait_vpn_connections_state


class Test_DescribeTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeTags, cls).setup_class()
        time_now = datetime.datetime.now()
        unique_id = time_now.strftime('%Y%m%d%H%M%S')
        cls.sg_name = 'sg_T111_{}'.format(unique_id)
        cls.dict_resources = {}
        Instance_Type = cls.a1_r1.config.region.get_info('default_instance_type')
        key_name = 'test_describe_keys_{}'.format(unique_id)
        # todo: create test for vpc peering
        try:
            # create security group
            sg_response = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=cls.sg_name)
            id_dict = 'sg0'
            cls.dict_resources[id_dict] = sg_response.response.groupId
            # create keypair
            cls.kp = cls.a1_r1.fcu.CreateKeyPair(KeyName=key_name)
            id_dict = 'kp0'
            cls.dict_resources[id_dict] = cls.kp.response.keyName
            ret = cls.a1_r1.fcu.CreateVolume(AvailabilityZone=cls.a1_r1.config.region.az_name, Size=1, VolumeType='standard')
            id_dict = 'vol0'
            cls.dict_resources[id_dict] = ret.response.volumeId
            wait_volumes_state(cls.a1_r1, [cls.dict_resources['vol0']], state='available')
            ret = cls.a1_r1.fcu.CreateSnapshot(VolumeId=cls.dict_resources['vol0'])
            id_dict = 'snap0'
            cls.dict_resources[id_dict] = ret.response.snapshotId
            # run instance
            inst = cls.a1_r1.fcu.RunInstances(ImageId=cls.a1_r1.config.region._conf['centos7'], MaxCount='1',
                                              MinCount='1', InstanceType=Instance_Type)
            id_dict = 'inst0'
            cls.dict_resources[id_dict] = inst.response.instancesSet[0].instanceId
            # create internetgateway
            ret = cls.a1_r1.fcu.CreateInternetGateway()
            id_dict = 'igw0'
            cls.dict_resources[id_dict] = ret.response.internetGateway.internetGatewayId
            # create VPC
            vpc = cls.a1_r1.fcu.CreateVpc(CidrBlock='10.0.0.0/16')
            id_dict = 'vpc0'
            cls.dict_resources[id_dict] = vpc.response.vpc.vpcId
            # create VPC
            vpc = cls.a2_r1.fcu.CreateVpc(CidrBlock='192.0.0.0/16')
            id_dict = 'vpc1'
            cls.dict_resources[id_dict] = vpc.response.vpc.vpcId
            # create subnet 1
            ret = cls.a1_r1.fcu.CreateSubnet(CidrBlock='10.0.1.0/24', VpcId=cls.dict_resources['vpc0'])
            id_dict = 'subnet0'
            cls.dict_resources[id_dict] = ret.response.subnet.subnetId
            ret = cls.a1_r1.fcu.CreateRouteTable(VpcId=cls.dict_resources['vpc0'])
            id_dict = 'rtb0'
            cls.dict_resources[id_dict] = ret.response.routeTable.routeTableId
            ret = cls.a1_r1.fcu.CreateNetworkInterface(SubnetId=cls.dict_resources['subnet0'])
            id_dict = 'fni0'
            cls.dict_resources[id_dict] = ret.response.networkInterface.networkInterfaceId
            ret = create_customer_gateway(cls.a1_r1, bgp_asn=1, ip_address='12.12.12.12', typ='ipsec.1')
            id_dict = 'cgw0'
            cls.dict_resources[id_dict] = ret.response.customerGateway.customerGatewayId
            ret = cls.a1_r1.fcu.CreateVpnGateway(Type='ipsec.1')
            id_dict = 'vgw0'
            cls.dict_resources['vgw0'] = ret.response.vpnGateway.vpnGatewayId
            ret = cls.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=cls.dict_resources['cgw0'], Type='ipsec.1',
                                                    VpnGatewayId=cls.dict_resources['vgw0'])
            id_dict = 'vpn0'
            cls.dict_resources[id_dict] = ret.response.vpnConnection.vpnConnectionId
            ret = cls.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=cls.dict_resources['vpc0'], PeerVpcId=cls.dict_resources['vpc1'],
                                                           PeerOwnerId=cls.a2_r1.config.account.account_id)
            id_dict = 'pcx0'
            cls.dict_resources[id_dict] = ret.response.vpcPeeringConnection.vpcPeeringConnectionId
            # wait instance to become ready
            wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=[cls.dict_resources['inst0']], state='ready')
            # create internetgateway
            ret = cls.a1_r1.fcu.CreateImage(InstanceId=cls.dict_resources['inst0'], Name='OMI_t111_{}'.format(unique_id))
            id_dict = 'ami0'
            cls.dict_resources[id_dict] = ret.response.imageId
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.dict_resources['inst0']:
                cls.a1_r1.fcu.TerminateInstances(InstanceId=[cls.dict_resources['inst0']])
                # replace by wait function
                wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=[cls.dict_resources['inst0']], state='terminated')
            if cls.dict_resources['kp0']:
                cls.a1_r1.fcu.DeleteKeyPair(KeyName=cls.dict_resources['kp0'])
            if cls.dict_resources['sg0']:
                cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.dict_resources['sg0'])
            if cls.dict_resources['vol0']:
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.dict_resources['vol0'])
            if cls.dict_resources['snap0']:
                cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=cls.dict_resources['snap0'])
            if cls.dict_resources['igw0']:
                cls.a1_r1.fcu.DeleteInternetGateway(
                    InternetGatewayId=cls.dict_resources['igw0'])
            if cls.dict_resources['fni0']:
                cls.a1_r1.fcu.DeleteNetworkInterface(
                    NetworkInterfaceId=cls.dict_resources['fni0'])
            if cls.dict_resources['subnet0']:
                cls.a1_r1.fcu.DeleteSubnet(SubnetId=cls.dict_resources['subnet0'])
            if cls.dict_resources['rtb0']:
                cls.a1_r1.fcu.DeleteRouteTable(RouteTableId=cls.dict_resources['rtb0'])
            if cls.dict_resources['pcx0']:
                cls.a1_r1.fcu.DeleteVpcPeeringConnection(VpcPeeringConnectionId=cls.dict_resources['pcx0'])
            if cls.dict_resources['vpc0']:
                cls.a1_r1.fcu.DeleteVpc(VpcId=cls.dict_resources['vpc0'])
            if cls.dict_resources['vpc1']:
                cls.a2_r1.fcu.DeleteVpc(VpcId=cls.dict_resources['vpc1'])
            if cls.dict_resources['vpn0']:
                cls.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=cls.dict_resources['vpn0'])
                wait_vpn_connections_state(osc_sdk=cls.a1_r1, state='deleted', vpn_connection_id_list=[cls.dict_resources['vpn0']])
            if cls.dict_resources['vgw0']:
                cls.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=cls.dict_resources['vgw0'])
            if cls.dict_resources['cgw0']:
                cls.a1_r1.fcu.DeleteCustomerGateway(
                    CustomerGatewayId=cls.dict_resources['cgw0'])
            if cls.dict_resources['ami0']:
                cls.a1_r1.fcu.DeregisterImage(ImageId=cls.dict_resources['ami0'])
        finally:
            super(Test_DescribeTags, cls).teardown_class()
