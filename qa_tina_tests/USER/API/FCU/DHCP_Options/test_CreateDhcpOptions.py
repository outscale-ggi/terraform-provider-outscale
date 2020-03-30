from qa_test_tools.config.configuration import Configuration
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite, known_error, assert_code
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_dhcp_options
from qa_test_tools.misc import assert_error


class Test_CreateDhcpOptions(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateDhcpOptions, cls).setup_class()
        cls.dhcp_options_list = []

    @classmethod
    def teardown_class(cls):
        try:
            if cls.dhcp_options_list:
                cleanup_dhcp_options(osc_sdk=cls.a1_r1, dhcpOptionsIds=cls.dhcp_options_list)
        finally:
            super(Test_CreateDhcpOptions, cls).teardown_class()

    def validate_dhcp_options(self, ret, dhcp_conf):
        try:
            # get the domain-name-server configuration
            configuration_set = next((conf for conf in ret.response.dhcpOptions.dhcpConfigurationSet if conf.key == dhcp_conf['Key']))
            assert configuration_set, "No configuration found for the key {}".format(dhcp_conf['Key'])
            assert configuration_set.key == dhcp_conf['Key']
            # check length
            assert len(configuration_set.valueSet) == len(dhcp_conf['Value'])
            for i in range(len(configuration_set.valueSet)):
                assert configuration_set.valueSet[i].value == dhcp_conf['Value'][i]
        except AssertionError as error:
            raise error

    def add_to_dhcp_list(self, ret):
        dhcp_id = ret.response.dhcpOptions.dhcpOptionsId
        self.dhcp_options_list.append(dhcp_id)

    def test_T1485_no_param(self):
        try:
            self.a1_r1.fcu.CreateDhcpOptions()
            assert False, "Not supposed to suceed"
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Request is missing the following parameter: DhcpConfigurations')

    def test_T1500_invalid_key(self):
        try:
            dhcpconf = {'Key': 'foo', 'Value': ['foo']}
            self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
            assert False, "DHCP options should not be created with not supported keys "
        except OscApiException as error:
            assert_code(error, 400)
            assert error.error_code == 'InvalidParameterValue'

    def test_T1491_with_invalid_value_domain_name_servers(self):
        try:
            dhcpconf = {'Key': 'domain-name-servers', 'Value': ['foo']}
            self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
            assert False, "Not supposed to create a {} with invalid IP".format(dhcpconf['Key'])
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Request contains an invalid parameter")

    def test_T1486_with_domain_name_servers(self):
        dhcpconf = {'Key': 'domain-name-servers', 'Value': [Configuration.get('ipaddress', 'dns_google')]}
        ret = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
        self.add_to_dhcp_list(ret=ret)
        self.validate_dhcp_options(ret, dhcpconf)

    def test_T1487_with_max_domain_name_servers(self):
        dhcpconf = {'Key': 'domain-name-servers', 'Value': [Configuration.get('domain_name_servers', 'server1'), Configuration.get(
            'domain_name_servers', 'server2'), Configuration.get('domain_name_servers', 'server3'),
            Configuration.get('domain_name_servers', 'server4')]}
        ret = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
        self.add_to_dhcp_list(ret=ret)
        self.validate_dhcp_options(ret, dhcpconf)

    def test_T1488_with_outranged_domain_name_servers(self):
        dhcpconf = {'Key': 'domain-name-servers', 'Value': [Configuration.get('domain_name_servers', 'server1'), Configuration.get(
            'domain_name_servers', 'server2'), Configuration.get('domain_name_servers', 'server3'),
            Configuration.get('domain_name_servers', 'server4'), Configuration.get(
                'domain_name_servers', 'server5')]}
        ret = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
        self.add_to_dhcp_list(ret=ret)
        self.validate_dhcp_options(ret, dhcpconf)

    def test_T1489_with_domain_name(self):
        dhcpconf = {'Key': 'domain-name', 'Value': ['outscale.qa']}
        ret = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
        self.add_to_dhcp_list(ret=ret)
        self.validate_dhcp_options(ret, dhcpconf)

    def test_T1490_with_domain_mulitple_name(self):
        dhcpconf = {'Key': 'domain-name', 'Value': ['outscale1.qa outscale2.qa outscale3.qa outscale4.qa']}
        ret = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
        self.add_to_dhcp_list(ret=ret)
        self.validate_dhcp_options(ret, dhcpconf)

    def test_T1492_with_ntp_server(self):
        dhcpconf = {'Key': 'ntp-servers', 'Value': [Configuration.get('ntp_servers', 'fr1')]}
        ret = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
        self.add_to_dhcp_list(ret=ret)
        self.validate_dhcp_options(ret, dhcpconf)

    def test_T1499_with_ntp_server_dns(self):
        try:
            dhcpconf = {'Key': 'ntp-servers', 'Value': ['ntp1.outscale.net']}
            ret = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
            self.add_to_dhcp_list(ret=ret)
            self.validate_dhcp_options(ret, dhcpconf)
            assert False, 'Remove known error code'
        except OscApiException as error:
            known_error('TINA-4056', error)

    def test_T1494_with_multiple_ntp_servers(self):
        dhcpconf = {'Key': 'ntp-servers', 'Value': [Configuration.get('ntp_servers', 'fr1'), Configuration.get('ntp_servers', 'fr2'),
                                                    Configuration.get('ntp_servers', 'fr3'), Configuration.get('ntp_servers', 'fr4')]}
        ret = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
        self.add_to_dhcp_list(ret=ret)
        self.validate_dhcp_options(ret, dhcpconf)

    def test_T1496_with_outranged_ntp_servers(self):
        dhcpconf = {'Key': 'ntp-servers', 'Value': [Configuration.get('ntp_servers', 'fr1'), Configuration.get('ntp_servers', 'fr2'),
                                                    Configuration.get('ntp_servers', 'fr3'), Configuration.get('ntp_servers', 'fr4'),
                                                    Configuration.get('ntp_servers', 'fr5')]}
        ret = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
        self.add_to_dhcp_list(ret=ret)
        self.validate_dhcp_options(ret, dhcpconf)

    def test_T1497_with_invalid_value_ntp_servers(self):
        try:
            dhcpconf = {'Key': 'ntp-servers', 'Value': ['foo']}
            ret = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
            self.add_to_dhcp_list(ret=ret)
            self.validate_dhcp_options(ret, dhcpconf)
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Invalid IPv4 address: foo")

    def test_T1498_all_param(self):
        dhcpconf = {'Key': 'domain-name-servers', 'Value': [Configuration.get('domain_name_servers', 'server1'), Configuration.get(
            'domain_name_servers', 'server2'), Configuration.get('domain_name_servers', 'server3'),
            Configuration.get('domain_name_servers', 'server4')]}
        dhcpconf1 = {'Key': 'ntp-servers', 'Value': [Configuration.get('ntp_servers', 'fr1')]}
        dhcpconf2 = {'Key': 'domain-name', 'Value': ['outscale.qa']}
        ret = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf, dhcpconf1, dhcpconf2])
        self.add_to_dhcp_list(ret=ret)
        self.validate_dhcp_options(ret, dhcpconf)
        self.validate_dhcp_options(ret, dhcpconf1)
        self.validate_dhcp_options(ret, dhcpconf2)
