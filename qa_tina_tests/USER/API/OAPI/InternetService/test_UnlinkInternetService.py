import pytest

from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_tina_tools.tools.tina.wait_tools import wait_internet_gateways_state, wait_vpcs_state
from qa_test_tools.config.configuration import Configuration
from qa_sdk_common.exceptions.osc_exceptions import OscApiException


class Test_UnlinkInternetService(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UnlinkInternetService, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_UnlinkInternetService, cls).teardown_class()

    def test_T2246_valid_params(self):
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
            self.a1_r1.oapi.UnlinkInternetService(InternetServiceId=inet_id, NetId=net_id)
            ret_link = None
        finally:
            if ret_link:
                try:
                    self.a1_r1.oapi.UnlinkInternetService(InternetServiceId=inet_id, NetId=net_id)
                except:
                    pass
            if inet_id:
                try:
                    self.a1_r1.oapi.DeleteInternetService(InternetServiceId=inet_id)
                except:
                    pass
            if net_id:
                try:
                    self.a1_r1.oapi.DeleteNet(NetId=net_id)
                except:
                    pass

    def test_T2247_valid_params_dry_run(self):
        net_id = None
        inet_id = None
        ret_link = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            inet_id = self.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
            wait_internet_gateways_state(self.a1_r1, [inet_id], state='available')
            ret_link = self.a1_r1.oapi.LinkInternetService(InternetServiceId=inet_id, NetId=net_id)
            ret = self.a1_r1.oapi.UnlinkInternetService(InternetServiceId=inet_id, NetId=net_id, DryRun=True)
            assert_dry_run(ret)
        finally:
            if ret_link:
                try:
                    self.a1_r1.oapi.UnlinkInternetService(InternetServiceId=inet_id, NetId=net_id)
                except:
                    pass
            if inet_id:
                try:
                    self.a1_r1.oapi.DeleteInternetService(InternetServiceId=inet_id)
                except:
                    pass
            if net_id:
                try:
                    self.a1_r1.oapi.DeleteNet(NetId=net_id)
                except:
                    pass

    @pytest.mark.tag_sec_confidentiality
    def test_T3466_other_account(self):
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
            self.a2_r1.oapi.UnlinkInternetService(InternetServiceId=inet_id, NetId=net_id)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5001)
        finally:
            if ret_link:
                try:
                    self.a1_r1.oapi.UnlinkInternetService(InternetServiceId=inet_id, NetId=net_id)
                except:
                    pass
            if inet_id:
                try:
                    self.a1_r1.oapi.DeleteInternetService(InternetServiceId=inet_id)
                except:
                    pass
            if net_id:
                try:
                    self.a1_r1.oapi.DeleteNet(NetId=net_id)
                except:
                    pass
