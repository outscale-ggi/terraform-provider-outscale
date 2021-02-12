import pytest

from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import wait
from qa_tina_tools.tina.wait import wait_Subnets_state
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_vpcs_state, wait_volumes_state

RESOURCE_TYPES = ['vm', 'nic', 'virtual-private-gateway', 'vpn-connection']


class Test_ReadTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadTags, cls).setup_class()
        cls.net_id_list = []
        cls.vol_id_list = []
        cls.internet_service_id = None
        cls.vm_info = {}
        cls.inst_id = None
        cls.nic_id = None
        cls.subnet_id = None
        cls.vgw_id = None
        cls.cgw_id = None
        cls.vpn_id = None
        try:
            cls.vm_info = create_instances(cls.a1_r1)
            cls.inst_id = cls.vm_info[INSTANCE_ID_LIST][0]
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.inst_id], Tags=[{'Key': 'tyty', 'Value': 'tqtq'}])
            net = cls.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), Tenancy='default').response.Net
            cls.net_id_list.append(net.NetId)
            cls.net_id_list.append(cls.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), Tenancy='dedicated').response.Net.NetId)
            wait_vpcs_state(cls.a1_r1, cls.net_id_list, state='available')
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.net_id_list[0]], Tags=[{'Key': 'toto', 'Value': 'tata'}])
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.net_id_list[1]], Tags=[{'Key': 'tata', 'Value': 'titi'}])
            ret = cls.a1_r1.oapi.CreateSubnet(NetId=cls.net_id_list[0], IpRange='10.0.0.0/24')
            cls.subnet_id = ret.response.Subnet.SubnetId
            wait_Subnets_state(cls.a1_r1, [cls.subnet_id], state='available')
            ret = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id)
            cls.nic_id = ret.response.Nic.NicId
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.nic_id], Tags=[{'Key': 'nic', 'Value': 'nic_value'}])
            cls.internet_service_id = cls.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId
            cls.vol_id_list.append(cls.a1_r1.oapi.CreateVolume(SubregionName=cls.azs[0], Size=20).response.Volume.VolumeId)
            cls.vol_id_list.append(cls.a1_r1.oapi.CreateVolume(SubregionName=cls.azs[0], Size=4).response.Volume.VolumeId)
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.vol_id_list[0]], Tags=[{'Key': 'vol1', 'Value': 'tata'}])
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.vol_id_list[1]], Tags=[{'Key': 'vol2', 'Value': 'titi'}])
            wait_volumes_state(cls.a1_r1, cls.vol_id_list, state='available')
            cls.vgw_id = cls.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
            wait.wait_VirtualGateways_state(cls.a1_r1, [cls.vgw_id], state='available')
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.vgw_id], Tags=[{'Key': 'vgw', 'Value': 'vgw_val'}])
            cls.cgw_id = cls.a1_r1.oapi.CreateClientGateway(BgpAsn=65000, ConnectionType='ipsec.1',
                                                            PublicIp='11.0.0.1').response.ClientGateway.ClientGatewayId
            wait.wait_ClientGateways_state(cls.a1_r1, [cls.cgw_id], state='available')
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.inst_id], Tags=[{'Key': 'cgw', 'Value': 'cgw_val'}])
            resp = cls.a1_r1.oapi.CreateVpnConnection(ClientGatewayId=cls.cgw_id, VirtualGatewayId=cls.vgw_id,
                                                      ConnectionType='ipsec.1').response
            cls.vpn_id = resp.VpnConnection.VpnConnectionId
            wait.wait_VpnConnections_state(cls.a1_r1, [cls.vpn_id], state='available')
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.vpn_id], Tags=[{'Key': 'vpn', 'Value': 'vpn_val'}])

        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpn_id:
                try:
                    cls.a1_r1.oapi.DeleteVpnConnection(VpnConnectionId=cls.vpn_id)
                except:
                    pass
            if cls.cgw_id:
                try:
                    cls.a1_r1.oapi.DeleteClientGateway(ClientGatewayId=cls.cgw_id)
                except:
                    pass
            if cls.vgw_id:
                try:
                    cls.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=cls.vgw_id)
                except:
                    pass
            if cls.nic_id:
                try:
                    cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id)
                except:
                    pass
            if cls.subnet_id:
                try:
                    cls.a1_r1.oapi.DeleteSubnet(SubnetId=cls.subnet_id)
                except:
                    pass
            if cls.vm_info:
                delete_instances(cls.a1_r1, cls.vm_info)
            for net_id in cls.net_id_list:
                try:
                    cls.a1_r1.oapi.DeleteNet(NetId=net_id)
                except:
                    pass
            for vol_id in cls.vol_id_list:
                try:
                    cls.a1_r1.oapi.DeleteVolume(VolumeId=vol_id)
                except:
                    pass
            if cls.internet_service_id:
                try:
                    cls.a1_r1.oapi.DeleteInternetService(InternetServiceId=cls.internet_service_id)
                except:
                    pass
        finally:
            super(Test_ReadTags, cls).teardown_class()

    def test_T4668_ressource_types(self):
        for resource in RESOURCE_TYPES:
            ret = self.a1_r1.oapi.ReadTags(Filters={'ResourceTypes': [resource]}).response
            assert len(ret.Tags) >= 1
            for tag in ret.Tags:
                assert tag.ResourceType == resource

    def test_T2366_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadTags(DryRun=True)
        assert_dry_run(ret)

    def test_T2522_verify_response_content(self):
        ret = self.a1_r1.oapi.ReadTags().response
        assert hasattr(ret, 'ResponseContext'), 'ResponseContext does not exist in the response'
        for tag in ret.Tags:
            assert hasattr(tag, 'Key'), 'IpRange does not exist in the response'
            assert hasattr(tag, 'ResourceId'), 'NetId does not exist in the response'
            assert hasattr(tag, 'ResourceType'), 'State does not exist in the response'
            assert hasattr(tag, 'Value'), 'Tags does not exist in the response'

    def test_T4667_with_valid_multiple_filters(self):
        ret = self.a1_r1.oapi.ReadTags(Filters={'Keys': ['toto'], 'Values': ['tata'], "ResourceIds": [self.net_id_list[0]]}).response
        assert len(ret.Tags) == 1
        for tag in ret.Tags:
            assert tag.ResourceType == 'net'

    def test_T2523_with_valid_filter_resource_types(self):
        ret = self.a1_r1.oapi.ReadTags(Filters={'ResourceTypes': ['volume']}).response
        assert len(ret.Tags) == 2
        for tag in ret.Tags:
            assert tag.ResourceType == 'volume'

    def test_T2524_with_valid_filter_resource_id(self):
        ret = self.a1_r1.oapi.ReadTags(Filters={'ResourceIds': [self.net_id_list[0]]}).response
        assert len(ret.Tags) == 1
        assert ret.Tags[0].ResourceId == self.net_id_list[0]

    def test_T2525_with_valid_filter_keys(self):
        ret = self.a1_r1.oapi.ReadTags(Filters={'Keys': ['vol1']}).response
        assert len(ret.Tags) == 1
        assert ret.Tags[0].ResourceId == self.vol_id_list[0]

    def test_T2526_with_valid_filter_values(self):
        ret = self.a1_r1.oapi.ReadTags(Filters={'Values': ['titi']}).response
        assert len(ret.Tags) == 2

    @pytest.mark.tag_sec_confidentiality
    def test_T3441_with_other_account(self):
        ret = self.a2_r1.oapi.ReadTags().response
        assert not ret.Tags

    @pytest.mark.tag_sec_confidentiality
    def test_T3442_with_other_account_filters(self):
        ret = self.a2_r1.oapi.ReadTags(Filters={'Values': ['titi']}).response
        assert not ret.Tags
