from string import ascii_lowercase

from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import id_generator, assert_error
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_dhcp_options
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.wait_tools import wait_dhcp_options_association
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_tina_tools.tools.tina.delete_tools import delete_vpc


class Test_DeleteDhcpOptions(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteDhcpOptions, cls).setup_class()
        cls.vpc_info = None
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, igw=False)
            ret = cls.a1_r1.fcu.DescribeVpcs(VpcId=[cls.vpc_info[VPC_ID]])
            cls.default_dhcp_options = ret.response.vpcSet[0].dhcpOptionsId
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_DeleteDhcpOptions, cls).teardown_class()

    def setup_method(self, method):
        super(Test_DeleteDhcpOptions, self).setup_method(method)
        dhcpconf = {'Key': 'domain-name', 'Value': ['outscale.qa']}
        ret = self.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
        self.dhcp_id = ret.response.dhcpOptions.dhcpOptionsId

    def teardown_method(self, method):
        if self.dhcp_id:
            ret = self.a1_r1.fcu.DescribeVpcs()
            current_dhcp_options = ret.response.vpcSet[0].dhcpOptionsId
            if current_dhcp_options != self.default_dhcp_options:
                self.a1_r1.fcu.AssociateDhcpOptions(DhcpOptionsId=self.default_dhcp_options, VpcId=self.vpc_info[VPC_ID])
                wait_dhcp_options_association(osc_sdk=self.a1_r1, dhcp_id=self.default_dhcp_options, vpc_id=self.vpc_info[VPC_ID])
            cleanup_dhcp_options(self.a1_r1, dhcpOptionsIds=[self.dhcp_id])
        super(Test_DeleteDhcpOptions, self).teardown_method(method)

    def test_T1501_no_param(self):
        try:
            self.a1_r1.fcu.DeleteDhcpOptions()
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Request is missing the following parameter: DhcpOptionsId')

    def test_T1502_invalid_id_correct_format(self):
        try:
            invalid_id = 'dopt-{}'.format(id_generator(chars=ascii_lowercase), size=8)
            self.a1_r1.fcu.DeleteDhcpOptions(DhcpOptionsId=invalid_id)
        except OscApiException as error:
            assert_error(error, 400, 'DhcpOptionsNotFound', "The DHCP Options '{}' does not exist".format(invalid_id))

    def test_T1503_invalid_id_incorrect_format(self):
        try:
            invalid_id = 'dopt-{}'.format(id_generator(chars=ascii_lowercase), size=12)
            self.a1_r1.fcu.DeleteDhcpOptions(DhcpOptionsId=invalid_id)
        except OscApiException as error:
            assert_error(error, 400, 'DhcpOptionsNotFound', "The DHCP Options '{}' does not exist".format(invalid_id))

    def test_T1504_required_param(self):
        self.a1_r1.fcu.DeleteDhcpOptions(DhcpOptionsId=self.dhcp_id)
        self.dhcp_id = None

    def test_T1505_attached_dhcp_options(self):
        try:
            self.a1_r1.fcu.AssociateDhcpOptions(DhcpOptionsId=self.dhcp_id, VpcId=self.vpc_info[VPC_ID])
            wait_dhcp_options_association(osc_sdk=self.a1_r1, dhcp_id=self.dhcp_id, vpc_id=self.vpc_info[VPC_ID])
            self.a1_r1.fcu.DeleteDhcpOptions(DhcpOptionsId=self.dhcp_id)
        except OscApiException as error:
            # TODO
            # assert_error(error, 400, 'DependencyViolation', 'DhcpOptions has dependencies and cannot be deleted: {}'.format(self.dhcp_id))
            # assert_error(error, 400, 'DependencyViolation', 'Resource has a dependent object')
            assert_error(error, 400, 'DependencyViolation', None)

    def test_T1507_delete_default(self):
        try:
            self.a1_r1.fcu.DeleteDhcpOptions(DhcpOptionsId=self.default_dhcp_options)
        except OscApiException as error:
            assert_error(error, 400, 'DependencyViolation', None)
