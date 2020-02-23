from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.misc import assert_oapi_error, assert_dry_run
from qa_common_tools.config.configuration import Configuration
from qa_tina_tools.tools.tina.wait_tools import wait_vpcs_state
from osc_common.exceptions.osc_exceptions import OscApiException


class Test_CreateSubnet(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateSubnet, cls).setup_class()
        cls.net = None
        cls.subnet_id = None

    @classmethod
    def teardown_class(cls):
        super(Test_CreateSubnet, cls).teardown_class()

    def setup_method(self, method):
        self.net = None
        super(Test_CreateSubnet, self).setup_method(method)
        try:
            self.net = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), Tenancy='default').response.Net.NetId
            wait_vpcs_state(self.a1_r1, [self.net], state='available')
        except:
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.subnet_id:
                self.a1_r1.oapi.DeleteSubnet(SubnetId=self.subnet_id)
            if self.net:
                self.a1_r1.oapi.DeleteNet(NetId=self.net)
        finally:
            super(Test_CreateSubnet, self).teardown_method(method)

    def test_T2258_valid_params(self):
        resp = self.a1_r1.oapi.CreateSubnet(NetId=self.net, IpRange=Configuration.get('subnet', '10_0_1_0_24')).response.Subnet
        self.subnet_id = resp.SubnetId
        assert hasattr(resp, 'Tags'), 'Response has no attribute Tags'
        assert hasattr(resp, 'SubnetId'), 'Response has no attribute SubnetId'
        assert hasattr(resp, 'AvailableIpsCount'), 'Response has no attribute AvailableIpsCount'
        assert hasattr(resp, 'IpRange'), 'Response has no attribute IpRange'
        assert hasattr(resp, 'NetId'), 'Response has no attribute NetId'
        assert hasattr(resp, 'SubregionName'), 'Response has no attribute SubregionName'
        assert hasattr(resp, 'State'), 'Response has no attribute State'

    def test_T2259_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.CreateSubnet(NetId=self.net, IpRange=Configuration.get('subnet', '10_0_1_0_24'), DryRun=True)
        assert_dry_run(ret)

    def test_T2562_missing_net_id(self):
        try:
            self.a1_r1.oapi.CreateSubnet(IpRange=Configuration.get('subnet', '10_0_1_0_24'))
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'MissingParameter', '7000')

    def test_T2563_incorrect_net_id(self):
        try:
            self.a1_r1.oapi.CreateSubnet(NetId='xxx-12345678', IpRange=Configuration.get('subnet', '10_0_1_0_24'))
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4104')

    def test_T2564_unknown_net_id(self):
        try:
            self.a1_r1.oapi.CreateSubnet(NetId='vpc-12345678', IpRange=Configuration.get('subnet', '10_0_1_0_24'))
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidResource', '5065')

    def test_T2565_missing_cidr_block(self):
        try:
            self.a1_r1.oapi.CreateSubnet(NetId=self.net)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'MissingParameter', '7000')

    def test_T2566_incorrect_cidr_block(self):
        try:
            self.a1_r1.oapi.CreateSubnet(NetId=self.net, IpRange=Configuration.get('subnet_invalid', '10_0_0_0_42'))
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4047')

    def test_T2567_unknown_az(self):
        try:
            self.a1_r1.oapi.CreateSubnet(NetId=self.net, IpRange=Configuration.get('subnet', '10_0_1_0_24'),
                                         SubregionName='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidResource', '5009')

    def test_T2568_same_ip_range_for_two_subnet(self):
        self.subnet_id = self.a1_r1.oapi.CreateSubnet(NetId=self.net, IpRange=Configuration.get('subnet',
                                                                                                '10_0_1_0_24')).response.Subnet.SubnetId
        try:
            self.a1_r1.oapi.CreateSubnet(NetId=self.net, IpRange=Configuration.get('subnet', '10_0_1_0_24'))
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 409, 'ResourceConflict', '9058')

    def test_T2569_net_from_different_user(self):
        net_use2 = None
        try:
            net_use2 = self.a2_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), Tenancy='default').response
            wait_vpcs_state(self.a2_r1, [net_use2.Net.NetId], state='available')
            self.a1_r1.oapi.CreateSubnet(NetId=net_use2.Net.NetId, IpRange=Configuration.get('subnet', '10_0_1_0_24'))
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidResource', '5065')
        finally:
            if net_use2.Net.NetId:
                try:
                    self.a2_r1.oapi.DeleteNet(NetId=net_use2.Net.NetId)
                except:
                    pass

    def test_T2622_valid_az(self):
        self.subnet_id = self.a1_r1.oapi.CreateSubnet(NetId=self.net,
                                                      IpRange=Configuration.get('subnet', '10_0_1_0_24'),
                                                      SubregionName=self.azs[0]).response.Subnet.SubnetId
