import pytest

from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_vpcs_state


class Test_ReadNets(OscTestSuite):

    nb_nets = 2

    @classmethod
    def setup_class(cls):
        super(Test_ReadNets, cls).setup_class()
        cls.net_id_list = []
        try:
            net = cls.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), Tenancy='default').response.Net
            cls.net_id_list.append(net.NetId)
            cls.dhcp_id = net.DhcpOptionsSetId
            cls.net_id_list.append(cls.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), Tenancy='dedicated').response.Net.NetId)
            cls.net_id_list.append(cls.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId)
            wait_vpcs_state(cls.a1_r1, cls.net_id_list, state='available')
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.net_id_list[0]], Tags=[{'Key': 'toto', 'Value': 'tata'}])
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.net_id_list[1]], Tags=[{'Key': 'tata', 'Value': 'titi'}])
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.net_id_list[2]], Tags=[{'Key': 'toto', 'Value': 'titi'}])
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            for net_id in cls.net_id_list:
                try:
                    cls.a1_r1.oapi.DeleteNet(NetId=net_id)
                except:
                    pass
        finally:
            super(Test_ReadNets, cls).teardown_class()

    def test_T2236_valid_params(self):
        self.a1_r1.oapi.ReadNets()

    def test_T2237_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadNets(DryRun=True)
        assert_dry_run(ret)

    def test_T2396_verify_response_content(self):
        for net_resp in self.net_id_list:
            ret = self.a1_r1.oapi.ReadNets(Filters={'NetIds': [net_resp]}).response
            for net in ret.Nets:
                assert net.DhcpOptionsSetId, 'DhcpOptionsSetId does not exist in the response'
                assert hasattr(net, 'IpRange'), 'IpRange does not exist in the response'
                assert hasattr(net, 'NetId'), 'NetId does not exist in the response'
                assert hasattr(net, 'State'), 'State does not exist in the response'
                assert hasattr(net, 'Tags'), 'Tags does not exist in the response'
                for tag in net.Tags:
                    assert hasattr(tag, 'Key') and (tag.Key is not None), 'Key does not exist in the tag'
                    assert hasattr(tag, 'Value'), 'Value does not exist in the tag'
                assert hasattr(net, 'Tenancy') and net.Tenancy in ['default', 'dedicated'], 'Tenancy does not exist in the response'

    def test_T2397_with_valid_filter_DhcpOptionsSetIds(self):
        ret = self.a1_r1.oapi.ReadNets(Filters={'DhcpOptionsSetIds': [self.dhcp_id]}).response
        assert len(ret.Nets) == 3

    def test_T2398_with_valid_filter_IpRanges(self):
        ret = self.a1_r1.oapi.ReadNets(Filters={'IpRanges': [Configuration.get('vpc', '10_0_0_0_16')]}).response
        assert len(ret.Nets) == 3

    def test_T2399_with_valid_filter_NetIds(self):
        ret = self.a1_r1.oapi.ReadNets(Filters={'NetIds': [self.net_id_list[0]]}).response
        assert len(ret.Nets) == 1

    def test_T2400_with_valid_filter_States(self):
        ret = self.a1_r1.oapi.ReadNets(Filters={'States': ['available']}).response
        assert len(ret.Nets) == 3

    def test_T2401_with_valid_filter_TagKeys(self):
        ret = self.a1_r1.oapi.ReadNets(Filters={'TagKeys': ['toto']}).response
        assert len(ret.Nets) == 2

    def test_T2402_with_valid_filter_TagValues(self):
        ret = self.a1_r1.oapi.ReadNets(Filters={'TagValues': ['titi']}).response
        assert len(ret.Nets) == 2

    def test_T2403_with_valid_filter_Tags(self):
        ret = self.a1_r1.oapi.ReadNets(Filters={'Tags': ['toto=tata']}).response
        assert len(ret.Nets) == 1

    @pytest.mark.tag_sec_confidentiality
    def test_T3448_other_account(self):
        ret = self.a2_r1.oapi.ReadNets().response.Nets
        assert not ret

    @pytest.mark.tag_sec_confidentiality
    def test_T3450_other_account_with_filter(self):
        ret = self.a2_r1.oapi.ReadNets(Filters={'NetIds': self.net_id_list}).response.Nets
        assert not ret

    def test_T5062_with_is_default_Tags(self):
        ret = self.a1_r1.oapi.ReadNets(Filters={'IsDefault': False}).response
        assert len(ret.Nets) == 3
        ret = self.a1_r1.oapi.ReadNets(Filters={'IsDefault': True}).response
        assert len(ret.Nets) == 0
