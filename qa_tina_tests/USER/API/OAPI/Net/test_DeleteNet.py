import pytest

from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.config.configuration import Configuration
from qa_common_tools.misc import assert_dry_run, assert_oapi_error
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_vpcs_state


class Test_DeleteNet(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteNet, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteNet, cls).teardown_class()

    def test_T2234_valid_params(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T2235_valid_params_dry_run(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
            ret = self.a1_r1.oapi.DeleteNet(NetId=net_id, DryRun=True)
            assert_dry_run(ret)
        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T2392_without_param(self):
        try:
            self.a1_r1.oapi.DeleteNet()
            assert False, "call should not have been successful, missing param"
        except OscApiException as err:
            assert_oapi_error(err, 400, 'MissingParameter', '7000')

    def test_T2393_without_param_existing_net(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
            self.a1_r1.oapi.DeleteNet()
            assert False, "call should not have been successful, missing net id"
        except OscApiException as err:
            assert_oapi_error(err, 400, 'MissingParameter', '7000')
        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T2394_invalid_net_id(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
            self.a1_r1.oapi.DeleteNet(NetId='toto')
            assert False, "call should not have been successful, invalid net id"
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4104')
        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)

    @pytest.mark.tag_sec_confidentiality
    def test_T2395_delete_from_another_account(self):
        net_id = None
        try:
            net_id = self.a2_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            wait_vpcs_state(self.a2_r1, [net_id], state='available')
            self.a1_r1.oapi.DeleteNet(NetId=net_id)
            assert False, "call should not have been successful, invalid param"
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidResource', '5065')
        finally:
            if net_id:
                self.a2_r1.oapi.DeleteNet(NetId=net_id)
