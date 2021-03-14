import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_internet_gateways_state, wait_vpcs_state


class Test_LinkInternetService(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_LinkInternetService, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_LinkInternetService, cls).teardown_class()

    def test_T2244_valid_params(self):
        net_id = None
        inet_id = None
        ret_link = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            inet_id = self.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
            wait_internet_gateways_state(self.a1_r1, [inet_id], state='available')
            ret_link = self.a1_r1.oapi.LinkInternetService(InternetServiceId=inet_id, NetId=net_id)
            wait_internet_gateways_state(self.a1_r1, [inet_id], state='in-use')
        finally:
            if ret_link:
                try:
                    self.a1_r1.oapi.UnlinkInternetService(InternetServiceId=inet_id, NetId=net_id)
                except:
                    print('Could not unlink internet service')
            if inet_id:
                try:
                    self.a1_r1.oapi.DeleteInternetService(InternetServiceId=inet_id)
                except:
                    print('Could not delete internet service')
            if net_id:
                try:
                    self.a1_r1.oapi.DeleteNet(NetId=net_id)
                except:
                    print('Could not delete vpc')

    def test_T2245_valid_params_dry_run(self):
        net_id = None
        inet_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            inet_id = self.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
            wait_internet_gateways_state(self.a1_r1, [inet_id], state='available')
            ret = self.a1_r1.oapi.LinkInternetService(InternetServiceId=inet_id, NetId=net_id, DryRun=True)
            assert_dry_run(ret)
        finally:
            if inet_id:
                try:
                    self.a1_r1.oapi.DeleteInternetService(InternetServiceId=inet_id)
                except:
                    print('Could not delete internet service')
            if net_id:
                try:
                    self.a1_r1.oapi.DeleteNet(NetId=net_id)
                except:
                    print('Could not delete vpc')

    @pytest.mark.tag_sec_confidentiality
    def test_T3464_other_account(self):
        net_id = None
        inet_id = None
        ret_link = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            inet_id = self.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
            wait_internet_gateways_state(self.a1_r1, [inet_id], state='available')
            ret_link = self.a2_r1.oapi.LinkInternetService(InternetServiceId=inet_id, NetId=net_id)
            wait_internet_gateways_state(self.a1_r1, [inet_id], state='in-use')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5001)
        finally:
            if ret_link:
                try:
                    self.a2_r1.oapi.UnlinkInternetService(InternetServiceId=inet_id, NetId=net_id)
                except:
                    print('Could not unlink internet service')
            if inet_id:
                try:
                    self.a1_r1.oapi.DeleteInternetService(InternetServiceId=inet_id)
                except:
                    print('Could not delete internet service')
            if net_id:
                try:
                    self.a1_r1.oapi.DeleteNet(NetId=net_id)
                except:
                    print('Could not delete vpc')
