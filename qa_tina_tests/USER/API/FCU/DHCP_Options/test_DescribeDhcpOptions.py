
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina import create_tools, delete_tools
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_dhcp_options


def validate_dhcp_options(ret, dhcp_conf, dhcp_item):
    try:
        # get the domain-name-server configuration
        for optionset in ret.response.dhcpOptionsSet:
            if optionset.dhcpOptionsId == dhcp_item:
                configuration_set = next((confset for confset in optionset.dhcpConfigurationSet if confset.key == dhcp_conf['Key']))
                assert configuration_set, "No configuration found for the key {}".format(dhcp_conf['Key'])
                assert configuration_set.key == dhcp_conf['Key']
                # check length
                assert len(configuration_set.valueSet) == len(dhcp_conf['Value'])
                for i, val in enumerate(configuration_set.valueSet):
                    assert val.value == dhcp_conf['Value'][i]
    except AssertionError as error:
        raise error

DHCP_CONFIGS = [{'Key': 'domain-name', 'Value': ['outscale.qa']},
                {'Key': 'domain-name-servers', 'Value': [Configuration.get('domain_name_servers', 'server1'),
                                                         Configuration.get('domain_name_servers', 'server2'),
                                                         Configuration.get('domain_name_servers', 'server3'),
                                                         Configuration.get('domain_name_servers', 'server4')]},
                {'Key': 'ntp-servers', 'Value': [Configuration.get('ntp_servers', 'fr1')]},
                {'Key': 'domain-name', 'Value': ['outscale.qa']}]

class Test_DescribeDhcpOptions(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.dhcp_options_list = []
        cls.vpc_info = None
        super(Test_DescribeDhcpOptions, cls).setup_class()
        cls.vpc_info = create_tools.create_vpc(osc_sdk=cls.a1_r1)
        for i in range(4):
            cls.dhcp_options_list.append(cls.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[DHCP_CONFIGS[i]]).response.dhcpOptions.dhcpOptionsId)

    @classmethod
    def teardown_class(cls):
        try:
            if cls.dhcp_options_list:
                cleanup_dhcp_options(osc_sdk=cls.a1_r1, dhcpOptionsIds=cls.dhcp_options_list)
            if cls.vpc_info:
                delete_tools.delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_DescribeDhcpOptions, cls).teardown_class()

    def test_T1508_no_param(self):
        ret = self.a1_r1.fcu.DescribeDhcpOptions()
        # 4 DHCP options created and 1 per defaut
        assert len(ret.response.dhcpOptionsSet) == 5, ' The amount of DHCP options displayed, does not match the amount expected'
        validate_dhcp_options(ret=ret, dhcp_conf=DHCP_CONFIGS[0], dhcp_item=self.dhcp_options_list[0])
        validate_dhcp_options(ret=ret, dhcp_conf=DHCP_CONFIGS[1], dhcp_item=self.dhcp_options_list[1])
        validate_dhcp_options(ret=ret, dhcp_conf=DHCP_CONFIGS[2], dhcp_item=self.dhcp_options_list[2])

    def test_T1515_using_dhcpoption_id(self):
        ret = self.a1_r1.fcu.DescribeDhcpOptions(DhcpOptionsId=[self.dhcp_options_list[0]])
        # 3 DHCP options created and 1 per defaut
        assert len(ret.response.dhcpOptionsSet) == 1, ' The amount of DHCP options displayed, does not match the amount expected'
        validate_dhcp_options(ret=ret, dhcp_conf=DHCP_CONFIGS[0], dhcp_item=self.dhcp_options_list[0])

    def test_T1516_using_multiple_dhcpoption_id(self):
        ret = self.a1_r1.fcu.DescribeDhcpOptions(DhcpOptionsId=[self.dhcp_options_list[0], self.dhcp_options_list[1]])
        # 3 DHCP options created and 1 per defaut
        assert len(ret.response.dhcpOptionsSet) == 2, ' The amount of DHCP options displayed, does not match the amount expected'
        validate_dhcp_options(ret=ret, dhcp_conf=DHCP_CONFIGS[0], dhcp_item=self.dhcp_options_list[0])
        validate_dhcp_options(ret=ret, dhcp_conf=DHCP_CONFIGS[1], dhcp_item=self.dhcp_options_list[1])

    def test_T1518_using_filter_key(self):
        supported_keys = ['domain-name', 'domain-name-servers', 'ntp-servers']
        for key in supported_keys:
            filter_dict = {'Name': 'key', 'Value': key}
            ret = self.a1_r1.fcu.DescribeDhcpOptions(Filter=[filter_dict])
            assert len(ret.response.dhcpOptionsSet) == 5, ' The amount of DHCP options displayed, does not match the amount expected'

    def test_T1519_using_filter_value(self):
        filter_dict = {'Name': 'value', 'Value': DHCP_CONFIGS[0]['Value']}
        ret = self.a1_r1.fcu.DescribeDhcpOptions(Filter=[filter_dict])
        assert len(ret.response.dhcpOptionsSet) == 2, ' The amount of DHCP options displayed, does not match the amount expected'

    def test_T1522_invalid_filter(self):
        try:
            self.a1_r1.fcu.DescribeDhcpOptions(Filter='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, 'InvalidParameterValue', 'Unexpected parameter Filter')

    def test_T1523_invalid_filter_key(self):
        filter_dict = {'Name': 'key', 'Value': 'foo'}
        ret = self.a1_r1.fcu.DescribeDhcpOptions(Filter=[filter_dict])
        assert ret.response.dhcpOptionsSet is None

    def test_T1524_using_filter_value_non_existing(self):

        filter_dict = {'Name': 'value', 'Value': 'foo'}
        ret = self.a1_r1.fcu.DescribeDhcpOptions(Filter=[filter_dict])
        assert ret.response.dhcpOptionsSet is None

    def test_T5955_with_tag_filter(self):
        indexes, _ = misc.execute_tag_tests(self.a1_r1, 'DhcpOptions', self.dhcp_options_list,
                                            'fcu.DescribeDhcpOptions', 'dhcpOptionsSet.dhcpOptionsId')
        assert indexes == [5, 6, 7, 8, 9, 10]
        known_error('TINA-6757', 'Call does not support wildcard in key value of tag:key')
