import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_vpcs_state


class Test_LinkRouteTable(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.net_id = None
        cls.subnet_id = None
        cls.rt_id = None
        cls.link_id = None
        super(Test_LinkRouteTable, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_LinkRouteTable, cls).teardown_class()

    def setup_method(self, method):
        self.net_id = None
        self.subnet_id = None
        self.rt_id = None
        self.link_id = None
        OscTestSuite.setup_method(self, method)
        try:
            self.net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            wait_vpcs_state(self.a1_r1, [self.net_id], state='available')
            self.subnet_id = self.a1_r1.oapi.CreateSubnet(NetId=self.net_id,
                                                          IpRange=Configuration.get('subnet', '10_0_1_0_24')).response.Subnet.SubnetId
            self.rt_id = self.a1_r1.oapi.CreateRouteTable(NetId=self.net_id).response.RouteTable.RouteTableId
        except:
            try:
                self.teardown_method(method)
            finally:
                raise

    def teardown_method(self, method):
        try:
            if self.link_id:
                try:
                    self.a1_r1.oapi.UnlinkRouteTable(LinkRouteTableId=self.link_id)
                except:
                    print('Could not unlink route table')
            if self.rt_id:
                try:
                    self.a1_r1.oapi.DeleteRouteTable(RouteTableId=self.rt_id)
                except:
                    print('Could not delete route table')
            if self.subnet_id:
                try:
                    self.a1_r1.oapi.DeleteSubnet(SubnetId=self.subnet_id)
                except:
                    print('Could not delete subnet')
            if self.net_id:
                try:
                    self.a1_r1.oapi.DeleteNet(NetId=self.net_id)
                except:
                    print('Could not delete net')
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T2264_valid_params(self):
        self.link_id = self.a1_r1.oapi.LinkRouteTable(SubnetId=self.subnet_id, RouteTableId=self.rt_id).response.LinkRouteTableId

    def test_T2265_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.LinkRouteTable(SubnetId=self.subnet_id, RouteTableId=self.rt_id, DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3523_other_account(self):
        try:
            self.a2_r1.oapi.LinkRouteTable(SubnetId=self.subnet_id, RouteTableId=self.rt_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5046')
