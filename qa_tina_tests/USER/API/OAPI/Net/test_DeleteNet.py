import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from specs import check_oapi_error
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_dry_run
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.wait_tools import wait_vpcs_state


class Test_DeleteNet(OscTinaTest):

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
            check_oapi_error(err, 7000)

    def test_T2393_without_param_existing_net(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
            self.a1_r1.oapi.DeleteNet()
            assert False, "call should not have been successful, missing net id"
        except OscApiException as err:
            check_oapi_error(err, 7000)
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
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='toto', prefixes='vpc-')
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
            check_oapi_error(err, 5065, id=net_id)
        finally:
            if net_id:
                self.a2_r1.oapi.DeleteNet(NetId=net_id)
