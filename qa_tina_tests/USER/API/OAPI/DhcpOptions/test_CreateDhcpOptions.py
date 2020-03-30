from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_dhcp_options
from qa_test_tools.misc import assert_oapi_error
from qa_tina_tests.USER.API.OAPI.DhcpOptions.DhcpOptions import validate_dhcp_options


class Test_CreateDhcpOptions(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateDhcpOptions, cls).setup_class()
        cls.dhcp_options_list = []
        cls.default_domain_name = cls.a1_r1.config.region.name + '.compute.internal'

    @classmethod
    def teardown_class(cls):
        try:
            if cls.dhcp_options_list:
                cleanup_dhcp_options(osc_sdk=cls.a1_r1, dhcpOptionsIds=cls.dhcp_options_list)
        finally:
            super(Test_CreateDhcpOptions, cls).teardown_class()

    def add_to_dhcp_list(self, ret):
        dhcp_id = ret.DhcpOptionsSetId
        self.dhcp_options_list.append(dhcp_id)

    def test_T2863_no_param(self):
        try:
            self.a1_r1.oapi.CreateDhcpOptions()
            assert False, "Not supposed to succeed"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2864_with_invalid_value_domain_name_servers(self):
        try:
            self.a1_r1.oapi.CreateDhcpOptions(DomainNameServers=['foo'])
            assert False, "Not supposed to create a DomainNameServers with invalid IP"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T2865_with_domain_name_servers(self):
        domain_name_servers = [Configuration.get('ipaddress', 'dns_google')]
        ret = self.a1_r1.oapi.CreateDhcpOptions(DomainNameServers=domain_name_servers).response.DhcpOptionsSet
        self.add_to_dhcp_list(ret=ret)
        validate_dhcp_options(ret, expected_dhcp={'DomainName': self.default_domain_name,
                                                  'DomainNameServers': domain_name_servers, 'Default': False})

    def test_T2866_with_max_domain_name_servers(self):
        domain_name_servers = [Configuration.get('domain_name_servers', 'server1'),
                               Configuration.get('domain_name_servers', 'server2'),
                               Configuration.get('domain_name_servers', 'server3'),
                               Configuration.get('domain_name_servers', 'server4')]
        ret = self.a1_r1.oapi.CreateDhcpOptions(DomainNameServers=domain_name_servers).response.DhcpOptionsSet
        self.add_to_dhcp_list(ret=ret)
        validate_dhcp_options(ret, expected_dhcp={'DomainName': self.default_domain_name,
                                                  'DomainNameServers': domain_name_servers, 'Default': False})

    def test_T2867_with_outranged_domain_name_servers(self):
        domain_name_servers = [Configuration.get('domain_name_servers', 'server1'),
                               Configuration.get('domain_name_servers', 'server2'),
                               Configuration.get('domain_name_servers', 'server3'),
                               Configuration.get('domain_name_servers', 'server4'),
                               Configuration.get('domain_name_servers', 'server5')]
        ret = self.a1_r1.oapi.CreateDhcpOptions(DomainNameServers=domain_name_servers).response.DhcpOptionsSet
        self.add_to_dhcp_list(ret=ret)
        validate_dhcp_options(ret, expected_dhcp={'DomainName': self.default_domain_name,
                                                  'DomainNameServers': domain_name_servers, 'Default': False})

    def test_T2868_with_domain_name(self):
        domain_name = 'outscale.qa'
        ret = self.a1_r1.oapi.CreateDhcpOptions(DomainName=domain_name).response.DhcpOptionsSet
        self.add_to_dhcp_list(ret=ret)
        validate_dhcp_options(ret,
                              expected_dhcp={'DomainName': domain_name, 'DomainNameServers': ['OutscaleProvidedDNS'],
                                             'Default': False})

    def test_T2869_with_ntp_server(self):
        ntp_servers = [Configuration.get('ntp_servers', 'fr1')]
        ret = self.a1_r1.oapi.CreateDhcpOptions(NtpServers=ntp_servers).response.DhcpOptionsSet
        self.add_to_dhcp_list(ret=ret)
        validate_dhcp_options(ret, expected_dhcp={'DomainName': self.default_domain_name, 'NtpServers': ntp_servers,
                                                  'DomainNameServers': ['OutscaleProvidedDNS'], 'Default': False})

    def test_T2870_with_ntp_server_dns(self):
        try:
            ntp_servers = ['ntp1.outscale.net']
            ret = self.a1_r1.oapi.CreateDhcpOptions(NtpServers=ntp_servers).response.DhcpOptionsSet
            self.add_to_dhcp_list(ret=ret)
            validate_dhcp_options(ret, expected_dhcp={'DomainName': self.default_domain_name, 'NtpServers': ntp_servers,
                                                      'DomainNameServers': ['OutscaleProvidedDNS'], 'Default': False})
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2871_with_multiple_ntp_servers(self):
        ntp_servers = [Configuration.get('ntp_servers', 'fr1'), Configuration.get('ntp_servers', 'fr2'),
                       Configuration.get('ntp_servers', 'fr3'), Configuration.get('ntp_servers', 'fr4')]
        ret = self.a1_r1.oapi.CreateDhcpOptions(NtpServers=ntp_servers).response.DhcpOptionsSet
        self.add_to_dhcp_list(ret=ret)
        validate_dhcp_options(ret, expected_dhcp={'DomainName': self.default_domain_name, 'NtpServers': ntp_servers,
                                                  'DomainNameServers': ['OutscaleProvidedDNS'], 'Default': False})

    def test_T2872_with_outranged_ntp_servers(self):
        ntp_servers = [Configuration.get('ntp_servers', 'fr1'), Configuration.get('ntp_servers', 'fr2'),
                       Configuration.get('ntp_servers', 'fr3'), Configuration.get('ntp_servers', 'fr4'),
                       Configuration.get('ntp_servers', 'fr5')]
        ret = self.a1_r1.oapi.CreateDhcpOptions(NtpServers=ntp_servers).response.DhcpOptionsSet
        self.add_to_dhcp_list(ret=ret)
        validate_dhcp_options(ret, expected_dhcp={'DomainName': self.default_domain_name, 'NtpServers': ntp_servers,
                                                  'DomainNameServers': ['OutscaleProvidedDNS'], 'Default': False})

    def test_T2873_with_invalid_value_ntp_servers(self):
        try:
            ntp_servers = ['foo']
            ret = self.a1_r1.oapi.CreateDhcpOptions(NtpServers=ntp_servers).response.DhcpOptionsSet
            self.add_to_dhcp_list(ret=ret)
            assert False, "Not supposed to succeed"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2874_all_param(self):
        ntp_servers = [Configuration.get('ntp_servers', 'fr1')]
        domain_name = 'outscale.qa'
        domain_name_servers = [Configuration.get('domain_name_servers', 'server1'),
                               Configuration.get('domain_name_servers', 'server2'),
                               Configuration.get('domain_name_servers', 'server3'),
                               Configuration.get('domain_name_servers', 'server4')]
        ret = self.a1_r1.oapi.CreateDhcpOptions(DomainName=domain_name, DomainNameServers=domain_name_servers,
                                                NtpServers=ntp_servers).response.DhcpOptionsSet
        self.add_to_dhcp_list(ret=ret)
        validate_dhcp_options(ret, expected_dhcp={'DomainName': domain_name, 'DomainNameServers': domain_name_servers,
                                                  'NtpServers': ntp_servers, 'Default': False})
