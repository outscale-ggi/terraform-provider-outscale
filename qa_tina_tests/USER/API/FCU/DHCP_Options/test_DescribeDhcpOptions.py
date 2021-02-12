from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_dhcp_options


class Test_DescribeDhcpOptions(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeDhcpOptions, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeDhcpOptions, cls).teardown_class()

    def setup_method(self, method):
        super(Test_DescribeDhcpOptions, self).setup_method(method)
        try:
            self.dhcp_options_list = []
            self.dhcpconf = {'Key': 'domain-name', 'Value': ['outscale.qa']}

            self.dhcpconf1 = {'Key': 'domain-name-servers', 'Value': [Configuration.get('domain_name_servers', 'server1'), Configuration.get(
                'domain_name_servers', 'server2'), Configuration.get('domain_name_servers', 'server3'),
                Configuration.get('domain_name_servers', 'server4')]}
            self.dhcpconf2 = {'Key': 'ntp-servers', 'Value': [Configuration.get('ntp_servers', 'fr1')]}
            ret = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[self.dhcpconf])
            ret1 = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[self.dhcpconf1])
            ret2 = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[self.dhcpconf2])
            self.add_to_dhcp_list(ret=ret)
            self.add_to_dhcp_list(ret=ret1)
            self.add_to_dhcp_list(ret=ret2)
        except Exception as error:
            self.teardown_method(method)
            raise error

    def teardown_method(self, method):
        try:
            if self.dhcp_options_list:
                cleanup_dhcp_options(osc_sdk=self.a1_r1, dhcpOptionsIds=self.dhcp_options_list)
        finally:
            super(Test_DescribeDhcpOptions, self).teardown_method(method)

    def add_to_dhcp_list(self, ret):
        dhcp_id = ret.response.dhcpOptions.dhcpOptionsId
        self.dhcp_options_list.append(dhcp_id)

    def validate_dhcp_options(self, ret, dhcp_conf, dhcp_item):
        try:
            # get the domain-name-server configuration
            for optionset in ret.response.dhcpOptionsSet:
                if optionset.dhcpOptionsId == dhcp_item:
                    configuration_set = next((confset for confset in optionset.dhcpConfigurationSet if confset.key == dhcp_conf['Key']))
                    assert configuration_set, "No configuration found for the key {}".format(dhcp_conf['Key'])
                    assert configuration_set.key == dhcp_conf['Key']
                    # check length
                    assert len(configuration_set.valueSet) == len(dhcp_conf['Value'])
                    for i in range(len(configuration_set.valueSet)):
                        assert configuration_set.valueSet[i].value == dhcp_conf['Value'][i]
        except AssertionError as error:
            raise error

    def test_T1508_no_param(self):
        ret = self.a1_r1.fcu.DescribeDhcpOptions()
        # 3 DHCP options created and 1 per defaut
        assert len(ret.response.dhcpOptionsSet) == 3, ' The amount of DHCP options displayed, does not match the amount expected'
        self.validate_dhcp_options(ret=ret, dhcp_conf=self.dhcpconf, dhcp_item=self.dhcp_options_list[0])
        self.validate_dhcp_options(ret=ret, dhcp_conf=self.dhcpconf1, dhcp_item=self.dhcp_options_list[1])
        self.validate_dhcp_options(ret=ret, dhcp_conf=self.dhcpconf2, dhcp_item=self.dhcp_options_list[2])

    def test_T1515_using_dhcpoption_id(self):
        ret = self.a1_r1.fcu.DescribeDhcpOptions(DhcpOptionsId=[self.dhcp_options_list[0]])
        # 3 DHCP options created and 1 per defaut
        assert len(ret.response.dhcpOptionsSet) == 1, ' The amount of DHCP options displayed, does not match the amount expected'
        self.validate_dhcp_options(ret=ret, dhcp_conf=self.dhcpconf, dhcp_item=self.dhcp_options_list[0])

    def test_T1516_using_multiple_dhcpoption_id(self):
        ret = self.a1_r1.fcu.DescribeDhcpOptions(DhcpOptionsId=[self.dhcp_options_list[0], self.dhcp_options_list[1]])
        # 3 DHCP options created and 1 per defaut
        assert len(ret.response.dhcpOptionsSet) == 2, ' The amount of DHCP options displayed, does not match the amount expected'
        self.validate_dhcp_options(ret=ret, dhcp_conf=self.dhcpconf, dhcp_item=self.dhcp_options_list[0])
        self.validate_dhcp_options(ret=ret, dhcp_conf=self.dhcpconf1, dhcp_item=self.dhcp_options_list[1])

    def test_T1518_using_filter_key(self):
        supported_keys = ['domain-name', 'domain-name-servers', 'ntp-servers']
        for key in supported_keys:
            filter_dict = {'Name': 'key', 'Value': key}
            ret = self.a1_r1.fcu.DescribeDhcpOptions(Filter=[filter_dict])
            assert len(ret.response.dhcpOptionsSet) == 3, ' The amount of DHCP options displayed, does not match the amount expected'

    def test_T1519_using_filter_value(self):
        filter_dict = {'Name': 'value', 'Value': self.dhcpconf['Value']}
        ret = self.a1_r1.fcu.DescribeDhcpOptions(Filter=[filter_dict])
        # 3 DHCP options created and 1 per defaut
        assert len(ret.response.dhcpOptionsSet) == 1, ' The amount of DHCP options displayed, does not match the amount expected'

    def test_T1522_invalid_filter(self):
        try:
            self.a1_r1.fcu.DescribeDhcpOptions(Filter='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Unexpected parameter Filter')

    def test_T1523_invalid_filter_key(self):
        filter_dict = {'Name': 'key', 'Value': 'foo'}
        ret = self.a1_r1.fcu.DescribeDhcpOptions(Filter=[filter_dict])
        assert ret.response.dhcpOptionsSet is None

    def test_T1524_using_filter_value_non_existing(self):

        filter_dict = {'Name': 'value', 'Value': 'foo'}
        ret = self.a1_r1.fcu.DescribeDhcpOptions(Filter=[filter_dict])
        assert ret.response.dhcpOptionsSet is None
