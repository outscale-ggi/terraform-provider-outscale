from string import ascii_lowercase

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator, assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_dhcp_options, cleanup_vpcs
from qa_tina_tools.tools.tina.create_tools import create_vpc_old
from qa_tina_tools.tools.tina.wait_tools import wait_dhcp_options_association


class Test_DeleteDhcpOptions(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_id = None
        cls.dhcp_id = None
        super(Test_DeleteDhcpOptions, cls).setup_class()
        try:
            ret = create_vpc_old(cls.a1_r1, Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc_id = ret.response.vpc.vpcId
            ret = cls.a1_r1.fcu.DescribeVpcs()
            cls.default_dhcp_options = ret.response.vpcSet[0].dhcpOptionsId
        except Exception:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_id:
                cleanup_vpcs(osc_sdk=cls.a1_r1, vpc_id_list=[cls.vpc_id])
        finally:
            super(Test_DeleteDhcpOptions, cls).teardown_class()

    def setup_method(self, method):
        super(Test_DeleteDhcpOptions, self).setup_method(method)
        ret = self.a1_r1.oapi.CreateDhcpOptions(DomainName='outscale.qa')
        self.dhcp_id = ret.response.DhcpOptionsSet.DhcpOptionsSetId

    def teardown_method(self, method):
        if self.dhcp_id:
            ret = self.a1_r1.fcu.DescribeVpcs()
            current_dhcp_options = ret.response.vpcSet[0].dhcpOptionsId
            if current_dhcp_options != self.default_dhcp_options:
                self.a1_r1.fcu.AssociateDhcpOptions(DhcpOptionsId=self.default_dhcp_options, VpcId=self.vpc_id)
                wait_dhcp_options_association(osc_sdk=self.a1_r1, dhcp_id=self.default_dhcp_options, vpc_id=self.vpc_id)
            cleanup_dhcp_options(self.a1_r1, dhcpOptionsIds=[self.dhcp_id])
        super(Test_DeleteDhcpOptions, self).teardown_method(method)

    def test_T2876_no_param(self):
        try:
            self.a1_r1.oapi.DeleteDhcpOptions()
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2877_invalid_id_correct_format(self):
        try:
            invalid_id = 'dopt-{}'.format(id_generator(chars=ascii_lowercase), size=8)
            self.a1_r1.oapi.DeleteDhcpOptions(DhcpOptionsSetId=invalid_id)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')

    def test_T2878_invalid_id_incorrect_format(self):
        try:
            invalid_id = 'dopt-{}'.format(id_generator(chars=ascii_lowercase), size=12)
            self.a1_r1.oapi.DeleteDhcpOptions(DhcpOptionsSetId=invalid_id)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')

    def test_T2879_required_param(self):
        self.a1_r1.oapi.DeleteDhcpOptions(DhcpOptionsSetId=self.dhcp_id)
        self.dhcp_id = None

    def test_T2880_attached_dhcp_options(self):
        try:
            self.a1_r1.fcu.AssociateDhcpOptions(DhcpOptionsId=self.dhcp_id, VpcId=self.vpc_id)
            wait_dhcp_options_association(osc_sdk=self.a1_r1, dhcp_id=self.dhcp_id, vpc_id=self.vpc_id)
            self.a1_r1.oapi.DeleteDhcpOptions(DhcpOptionsSetId=self.dhcp_id)
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9029')

    def test_T2881_delete_default(self):
        try:
            self.a1_r1.oapi.DeleteDhcpOptions(DhcpOptionsSetId=self.default_dhcp_options)
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9029')

    @pytest.mark.tag_sec_confidentiality
    def test_T3543_with_other_user(self):
        try:
            self.a2_r1.oapi.DeleteDhcpOptions(DhcpOptionsSetId=self.dhcp_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5018')

    def test_T3540_valid_dry_run(self):
        self.a2_r1.oapi.DeleteDhcpOptions(DhcpOptionsSetId=self.dhcp_id, DryRun=True)
