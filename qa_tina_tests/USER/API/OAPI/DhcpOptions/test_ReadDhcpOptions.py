import pytest

from qa_test_tools.config.configuration import Configuration
from qa_test_tools.test_base import OscTestSuite, get_export_value
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_dhcp_options
from qa_tina_tests.USER.API.OAPI.DhcpOptions.DhcpOptions import validate_dhcp_options
from qa_test_tools.misc import assert_dry_run


class Test_ReadDhcpOptions(OscTestSuite):

    @classmethod
    def add_to_dhcp_list(self, ret):
        dhcp_id = ret.DhcpOptionsSetId
        self.dhcp_options_list.append(dhcp_id)

    @classmethod
    def setup_class(cls):
        cls.dhcp_options_list = []
        super(Test_ReadDhcpOptions, cls).setup_class()
        try:
            cls.ntp_servers = [Configuration.get('ntp_servers', 'fr1')]
            cls.domain_name = 'outscale.qa'
            cls.default_domain_name = cls.a1_r1.config.region.name + '.compute.internal'
            cls.domain_name_servers = [Configuration.get('domain_name_servers', 'server1'),
                                       Configuration.get('domain_name_servers', 'server2'),
                                       Configuration.get('domain_name_servers', 'server3'),
                                       Configuration.get('domain_name_servers', 'server4')]
            ret = cls.a1_r1.oapi.CreateDhcpOptions(DomainName=cls.domain_name).response.DhcpOptionsSet
            cls.dhcp_options_list.append(ret.DhcpOptionsSetId)
            ret = cls.a1_r1.oapi.CreateDhcpOptions(DomainNameServers=cls.domain_name_servers).response.DhcpOptionsSet
            cls.dhcp_options_list.append(ret.DhcpOptionsSetId)
            ret = cls.a1_r1.oapi.CreateDhcpOptions(NtpServers=cls.ntp_servers).response.DhcpOptionsSet
            cls.dhcp_options_list.append(ret.DhcpOptionsSetId)
            ret = cls.a1_r1.oapi.CreateDhcpOptions(DomainName=cls.domain_name,
                                                   DomainNameServers=cls.domain_name_servers,
                                                   NtpServers=cls.ntp_servers).response.DhcpOptionsSet
            cls.dhcp_options_list.append(ret.DhcpOptionsSetId)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.dhcp_options_list:
                cleanup_dhcp_options(osc_sdk=cls.a1_r1, dhcpOptionsIds=cls.dhcp_options_list)
        finally:
            super(Test_ReadDhcpOptions, cls).teardown_class()

    def test_T2882_no_param(self):
        ret = self.a1_r1.oapi.ReadDhcpOptions()
        ret.check_response()
        ret = ret.response.DhcpOptionsSets
        # 4 DHCP options created and 1 per defaut
        assert len(ret) >= 4, ' The amount of DHCP options displayed, does not match the amount expected'
        for dhcp in ret:
            if dhcp.DhcpOptionsSetId == self.dhcp_options_list[0]:
                validate_dhcp_options(dhcp, expected_dhcp={'DomainName': self.domain_name,
                                                           'DomainNameServers': ['OutscaleProvidedDNS'],
                                                           'Default': False})
            if dhcp.DhcpOptionsSetId == self.dhcp_options_list[1]:
                validate_dhcp_options(dhcp,
                                      expected_dhcp={'DomainName': self.default_domain_name,
                                                     'DomainNameServers': self.domain_name_servers,
                                                     'Default': False})
            if dhcp.DhcpOptionsSetId == self.dhcp_options_list[2]:
                validate_dhcp_options(dhcp,
                                      expected_dhcp={'DomainName': self.default_domain_name,
                                                     'DomainNameServers': ['OutscaleProvidedDNS'],
                                                     'NtpServers': self.ntp_servers, 'Default': False})
            if dhcp.DhcpOptionsSetId == self.dhcp_options_list[3]:
                validate_dhcp_options(dhcp, expected_dhcp={'DomainName': self.domain_name,
                                                           'DomainNameServers': self.domain_name_servers,
                                                           'NtpServers': self.ntp_servers, 'Default': False})

    def test_T2883_filters_dhcpoption_id(self):
        ret = self.a1_r1.oapi.ReadDhcpOptions(Filters={'DhcpOptionsSetIds': [self.dhcp_options_list[0]]}).response.DhcpOptionsSets
        assert len(ret) == 1, ' The amount of DHCP options displayed, does not match the amount expected'
        validate_dhcp_options(ret[0], expected_dhcp={'DomainName': self.domain_name,
                                                     'DomainNameServers': ['OutscaleProvidedDNS'], 'Default': False,
                                                     'DhcpOptionsSetId': self.dhcp_options_list[0]})

    def test_T2884_filters_multiple_dhcpoption_id(self):
        ret = self.a1_r1.oapi.ReadDhcpOptions(
            Filters={'DhcpOptionsSetIds': [self.dhcp_options_list[0], self.dhcp_options_list[1]]}).response.DhcpOptionsSets
        assert len(ret) == 2, ' The amount of DHCP options displayed, does not match the amount expected'
        for dhcp in ret:
            if dhcp.DhcpOptionsSetId == self.dhcp_options_list[0]:
                validate_dhcp_options(dhcp, expected_dhcp={'DomainName': self.domain_name,
                                                           'DomainNameServers': ['OutscaleProvidedDNS'],
                                                           'Default': False})
            elif dhcp.DhcpOptionsSetId == self.dhcp_options_list[1]:
                validate_dhcp_options(dhcp,
                                      expected_dhcp={'DomainName': self.default_domain_name,
                                                     'DomainNameServers': self.domain_name_servers,
                                                     'Default': False})
            else:
                assert False, 'We have filtered by Id, we do not have the right id : {}/{}'.format(
                    dhcp.DhcpOptionsSetId, [self.dhcp_options_list[0], self.dhcp_options_list[1]])

    def test_T2885_filters_default(self):
        ret = self.a1_r1.oapi.ReadDhcpOptions(Filters={'Default': True}).response.DhcpOptionsSets
        for dhcp in ret:
            validate_dhcp_options(dhcp, expected_dhcp={'Default': True})
        ret = self.a1_r1.oapi.ReadDhcpOptions(Filters={'Default': False}).response.DhcpOptionsSets
        if get_export_value('OSC_CU') and len(self.azs) == 1:
            assert len(ret) == 4, ' The amount of DHCP options displayed, does not match the amount expected'
        else:
            assert len(ret) == 5, ' The amount of DHCP options displayed, does not match the amount expected'
        for dhcp in ret:
            validate_dhcp_options(dhcp, expected_dhcp={'Default': False})

    def test_T2886_filters_ntp_servers(self):
        ret = self.a1_r1.oapi.ReadDhcpOptions(Filters={'NtpServers': [self.ntp_servers[0]]}).response.DhcpOptionsSets
        assert len(ret) == 2, ' The amount of DHCP options displayed, does not match the amount expected'
        for dhcp in ret:
            validate_dhcp_options(dhcp, expected_dhcp={'NtpServers': self.ntp_servers})

    def test_T2887_filters_domain_name(self):
        ret = self.a1_r1.oapi.ReadDhcpOptions(Filters={'DomainNames': [self.domain_name]}).response.DhcpOptionsSets
        if get_export_value('OSC_CU') and len(self.azs) == 1:
            assert len(ret) == 2, ' The amount of DHCP options displayed, does not match the amount expected'
        else:
            assert len(ret) == 3, ' The amount of DHCP options displayed, does not match the amount expected'
        for dhcp in ret:
            validate_dhcp_options(dhcp, expected_dhcp={'DomainName': self.domain_name})

    def test_T2888_filters_domain_name_servers(self):
        ret = self.a1_r1.oapi.ReadDhcpOptions(Filters={'DomainNameServers': [self.domain_name_servers[2]]}).response.DhcpOptionsSets
        assert len(ret) == 2, ' The amount of DHCP options displayed, does not match the amount expected'
        for dhcp in ret:
            validate_dhcp_options(dhcp, expected_dhcp={'DomainNameServers': self.domain_name_servers})

    def test_T3451_dry_run(self):
        ret = self.a1_r1.oapi.ReadDhcpOptions()
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3452_other_account(self):
        ret = self.a2_r1.oapi.ReadDhcpOptions().response.DhcpOptionsSets
        if get_export_value('OSC_CU') and len(self.azs) == 1:
            assert not ret
        else:
            assert len(ret) == 1

    @pytest.mark.tag_sec_confidentiality
    def test_T3453_other_account_with_filter(self):
        ret = self.a2_r1.oapi.ReadDhcpOptions(Filters={'DhcpOptionsSetIds': self.dhcp_options_list}).response.DhcpOptionsSets
        assert not ret
