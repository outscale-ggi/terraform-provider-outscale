import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.create_tools import create_vpc_old


class Test_UpdateNet(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateNet, cls).setup_class()
        cls.vpc_id = None
        try:
            ret = create_vpc_old(cls.a1_r1, Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc_id = ret.response.vpc.vpcId
            ret = cls.a1_r1.fcu.DescribeVpcs()
            cls.default_dhcp_options = ret.response.vpcSet[0].dhcpOptionsId
            cls.dopt_id = cls.a1_r1.oapi.CreateDhcpOptions(
                DomainName='outscale.qa').response.DhcpOptionsSet.DhcpOptionsSetId
        except Exception:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_id:
                cleanup_vpcs(osc_sdk=cls.a1_r1, vpc_id_list=[cls.vpc_id])
            if cls.dopt_id:
                cls.a1_r1.oapi.DeleteDhcpOptions(DhcpOptionsSetId=cls.dopt_id)
        finally:
            super(Test_UpdateNet, cls).teardown_class()

    def test_T2889_empty_param(self):
        try:
            self.a1_r1.oapi.UpdateNet()
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2890_missing_param(self):
        try:
            self.a1_r1.oapi.UpdateNet(DhcpOptionsSetId=self.default_dhcp_options)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.UpdateNet(NetId=self.vpc_id)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2891_invalid_param(self):
        try:
            self.a1_r1.oapi.UpdateNet(DhcpOptionsSetId='tata', NetId=self.vpc_id)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')
        try:
            self.a1_r1.oapi.UpdateNet(DhcpOptionsSetId='dopt-12345678', NetId=self.vpc_id)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5018')
        try:
            self.a1_r1.oapi.UpdateNet(DhcpOptionsSetId=self.dopt_id, NetId='tata')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')
        try:
            self.a1_r1.oapi.UpdateNet(DhcpOptionsSetId=self.dopt_id, NetId='vpc-12345678')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5065')

    def test_T2892_valid_param(self):
        net = self.a1_r1.oapi.UpdateNet(DhcpOptionsSetId=self.dopt_id, NetId=self.vpc_id).response.Net
        assert hasattr(net, 'DhcpOptionsSetId'), 'DhcpOptionsSetId does not exist in the response'
        assert hasattr(net, 'IpRange'), 'IpRange does not exist in the response'
        assert hasattr(net, 'NetId'), 'NetId does not exist in the response'
        assert hasattr(net, 'State'), 'State does not exist in the response'
        assert hasattr(net, 'Tags'), 'Tags does not exist in the response'
        for tag in net.Tags:
            assert hasattr(tag, 'Key') and (tag.Key is not None), 'Key does not exist in the tag'
            assert hasattr(tag, 'Value'), 'Value does not exist in the tag'
        assert hasattr(net, 'Tenancy') and net.Tenancy in ['default', 'dedicated'], 'Tenancy does not exist in the response'
        assert self.a1_r1.oapi.UpdateNet(DhcpOptionsSetId=self.dopt_id, NetId=self.vpc_id)

    def test_T3480_dry_run(self):
        ret = self.a1_r1.oapi.UpdateNet(DhcpOptionsSetId=self.dopt_id, NetId=self.vpc_id, DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3481_other_account(self):
        dopt_id = self.a2_r1.oapi.CreateDhcpOptions(DomainName='outscale.qa').response.DhcpOptionsSet.DhcpOptionsSetId
        try:
            self.a2_r1.oapi.UpdateNet(DhcpOptionsSetId=dopt_id, NetId=self.vpc_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5065)

    def test_T4903_with_default_dhcpoptions(self):
        self.a1_r1.oapi.UpdateNet(DhcpOptionsSetId="default", NetId=self.vpc_id)
