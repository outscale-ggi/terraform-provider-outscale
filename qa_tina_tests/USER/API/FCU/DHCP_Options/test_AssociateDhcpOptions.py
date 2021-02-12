from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.create_tools import create_vpc_old
from qa_tina_tools.tools.tina.wait_tools import wait_dhcp_options_association


class Test_AssociateDhcpOptions(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_id = None
        super(Test_AssociateDhcpOptions, cls).setup_class()
        try:
            ret = create_vpc_old(cls.a1_r1, Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc_id = ret.response.vpc.vpcId
            ret = cls.a1_r1.fcu.DescribeVpcs()
            cls.default_dhcp_options = ret.response.vpcSet[0].dhcpOptionsId
        except Exception as error:
            cls.teardown_class()
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_id:
                cleanup_vpcs(osc_sdk=cls.a1_r1, vpc_id_list=[cls.vpc_id])
        finally:
            super(Test_AssociateDhcpOptions, cls).teardown_class()

    def setup_method(self, method):
        super(Test_AssociateDhcpOptions, self).setup_method(method)
        dhcpconf = {'Key': 'domain-name', 'Value': ['outscale.qa']}
        ret = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
        self.dhcp_id = ret.response.dhcpOptions.dhcpOptionsId

    def teardown_method(self, method):
        if self.dhcp_id:
            ret = self.a1_r1.fcu.DescribeVpcs()
            current_dhcp_options = ret.response.vpcSet[0].dhcpOptionsId
            if current_dhcp_options != self.default_dhcp_options:
                self.a1_r1.fcu.AssociateDhcpOptions(DhcpOptionsId=self.default_dhcp_options, VpcId=self.vpc_id)
                wait_dhcp_options_association(osc_sdk=self.a1_r1, vpc_id=self.vpc_id, dhcp_id=self.default_dhcp_options)
        super(Test_AssociateDhcpOptions, self).teardown_method(method)

    def test_T1509_no_param(self):
        try:
            self.a1_r1.fcu.AssociateDhcpOptions()
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Request is missing the following parameter: VpcId, DhcpOptionsId")

    def test_T1510_no_vpc_id(self):
        try:
            self.a1_r1.fcu.AssociateDhcpOptions(DhcpOptionsId=self.dhcp_id)
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Request is missing the following parameter: VpcId")

    def test_T1511_no_dhcpoptions_id(self):
        try:
            self.a1_r1.fcu.AssociateDhcpOptions(VpcId=self.vpc_id)
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Request is missing the following parameter: DhcpOptionsId")

    def test_T1512_required_param(self):
        self.a1_r1.fcu.AssociateDhcpOptions(VpcId=self.vpc_id, DhcpOptionsId=self.dhcp_id)
        wait_dhcp_options_association(osc_sdk=self.a1_r1, dhcp_id=self.dhcp_id, vpc_id=self.vpc_id)
        ret = self.a1_r1.fcu.DescribeVpcs(VpcId=[self.vpc_id])
        current_dhcp_options = ret.response.vpcSet[0].dhcpOptionsId
        assert current_dhcp_options == self.dhcp_id, "DHCP options has not been associated succesfully"

    def test_T1513_invalid_dhcpoptions_id(self):
        try:
            self.a1_r1.fcu.AssociateDhcpOptions(VpcId=self.vpc_id, DhcpOptionsId='foo')
        except OscApiException as error:
            assert_error(error, 400, "DhcpOptionsNotFound", "The DHCP Options 'foo' does not exist")

    def test_T1514_invalid_vpc_id(self):
        try:
            self.a1_r1.fcu.AssociateDhcpOptions(VpcId='foo', DhcpOptionsId=self.dhcp_id)
        except OscApiException as error:
            assert_error(error, 400, "InvalidVpcID.NotFound", "The vpc ID 'foo' does not exist")

    def test_T1600_set_default_options(self):
        self.a1_r1.fcu.AssociateDhcpOptions(DhcpOptionsId='default', VpcId=self.vpc_id)
