
from qa_common_tools.config.configuration import Configuration
from qa_common_tools.test_base import OscTestSuite


class Test_find(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_find, cls).setup_class()
        cls.dhcp_options_list = []
        cls.dhcpconf = {'Key': 'domain-name', 'Value': ['outscale.qa']}
        cls.dhcpconf1 = {'Key': 'domain-name-servers', 'Value': [Configuration.get('domain_name_servers', 'server1'), Configuration.get(
            'domain_name_servers', 'server2'), Configuration.get('domain_name_servers', 'server3'),
            Configuration.get('domain_name_servers', 'server4')]}
        cls.dhcpconf2 = {'Key': 'ntp-servers', 'Value': [Configuration.get('ntp_servers', 'fr1')]}
        ret = cls.a1_r1.intel.dhcpoptions.create(owner=cls.a1_r1.config.account.account_id, options={'domain-name': ['outscale.qa'],
                                                                                                     'domain-name-servers': [Configuration.get(
                                                                                                         'domain_name_servers', 'server1')]})
        cls.dhcp_options_list.append(ret.response.result.id)

        ret = cls.a1_r1.intel.dhcpoptions.create(owner=cls.a1_r1.config.account.account_id, options={'domain-name': ['outscale.qa']})
        cls.dhcp_options_list.append(ret.response.result.id)
        ret = cls.a1_r1.intel.dhcpoptions.create(owner=cls.a1_r1.config.account.account_id, options={'domain-name': ['outscale.qa'],
                                                                                                     'domain-name-servers': [Configuration.get(
                                                                                                         'domain_name_servers', 'server1')],
                                                                                                     'ntp-servers': [Configuration.get(
                                                                                                         'ntp_servers', 'fr1')]})

        cls.dhcp_options_list.append(ret.response.result.id)

    @classmethod
    def teardown_class(cls):
        try:
            if cls.dhcp_options_list:
                for dhcpop in cls.dhcp_options_list:
                    cls.a1_r1.intel.dhcpoptions.delete(dhcpoptions_id=dhcpop, owner=cls.a1_r1.config.account.account_id)
        finally:
            super(Test_find, cls).teardown_class()

    def test_T2995_find_with_valid_ntp_servers(self):
        ret = self.a1_r1.intel.dhcpoptions.find(owner=self.a1_r1.config.account.account_id, ntp_servers=[Configuration.get('ntp_servers', 'fr1')])
        assert len(ret.response.result) == 1

    def test_T2996_find_with_invalid_ntp_servers(self):
        ret = self.a1_r1.intel.dhcpoptions.find(owner=self.a1_r1.config.account.account_id, ntp_servers='toto')
        assert len(ret.response.result) == 0

    def test_T2997_find_with_valid_domain_name_servers(self):
        ret = self.a1_r1.intel.dhcpoptions.find(owner=self.a1_r1.config.account.account_id, domain_name_servers=[Configuration.get(
            'domain_name_servers', 'server1')])
        assert len(ret.response.result) == 2

    def test_T2998_find_with_invalid_domain_name_servers(self):
        ret = self.a1_r1.intel.dhcpoptions.find(owner=self.a1_r1.config.account.account_id, domain_name_servers='toto')
        assert len(ret.response.result) == 0

    def test_T2999_find_with_valid_domain_name(self):
        ret = self.a1_r1.intel.dhcpoptions.find(owner=self.a1_r1.config.account.account_id, domain_name='outscale.qa')
        assert len(ret.response.result) == 3

    def test_T3000_find_with_invalid_domain_name(self):
        ret = self.a1_r1.intel.dhcpoptions.find(owner=self.a1_r1.config.account.account_id, domain_name='toto')
        assert len(ret.response.result) == 0
