import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina import wait_tools
from specs import check_oapi_error

NUM_INTERNET_SERVICES = 4


class Test_ReadInternetServices(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.is_ids = []
        super(Test_ReadInternetServices, cls).setup_class()
        cls.ret_link = None
        cls.net_id = None
        try:
            for _ in range(NUM_INTERNET_SERVICES):
                net_id = cls.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId
                cls.is_ids.append(net_id)

            cls.net_id = cls.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            wait_tools.wait_vpcs_state(cls.a1_r1, [cls.net_id], state='available')
            wait_tools.wait_internet_gateways_state(cls.a1_r1, [cls.is_ids[0]], state='available')
            cls.ret_link = cls.a1_r1.oapi.LinkInternetService(InternetServiceId=cls.is_ids[0], NetId=cls.net_id)
            wait_tools.wait_internet_gateways_state(cls.a1_r1, [cls.is_ids[0]], state='in-use')
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        if cls.ret_link:
            try:
                cls.a1_r1.oapi.UnlinkInternetService(InternetServiceId=cls.is_ids[0], NetId=cls.net_id)
            except:
                print('Could not unlink internet service')
        if cls.net_id:
            try:
                cls.a1_r1.oapi.DeleteNet(NetId=cls.net_id)
            except:
                print('Could not delete net')
        try:
            for net_id in cls.is_ids:
                cls.a1_r1.oapi.DeleteInternetService(InternetServiceId=net_id)
        finally:
            super(Test_ReadInternetServices, cls).teardown_class()

    def test_T2242_valid_params(self):
        self.a1_r1.oapi.ReadInternetServices()

    def test_T2243_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadInternetServices(DryRun=True)
        misc.assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3429_other_account(self):
        ret = self.a2_r1.oapi.ReadInternetServices().response.InternetServices
        assert not ret

    @pytest.mark.tag_sec_confidentiality
    def test_T3430_other_account_with_filter(self):
        ret = self.a2_r1.oapi.ReadInternetServices(Filters={'InternetServiceIds': self.is_ids}).response.InternetServices
        assert not ret

    def test_T3827_with_internet_service_ids_filter(self):
        ret = self.a1_r1.oapi.ReadInternetServices(Filters={'InternetServiceIds': [self.is_ids[0]]})
        assert len(ret.response.InternetServices) == 1

    def test_T3828_multi_internet_service_no_capa(self):
        try:
            for _ in range(6):
                self.is_ids.append(self.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId)
        except OscApiException as err:
            check_oapi_error(err, 10023)

    def test_T5067_with_link_net_ids_filter(self):
        ret = self.a1_r1.oapi.ReadInternetServices(Filters={'LinkNetIds': [self.net_id]})
        assert len(ret.response.InternetServices) == 1

    def test_T5068_with_link_state_filter(self):
        ret = self.a1_r1.oapi.ReadInternetServices(Filters={'LinkStates': ["available"]})
        assert len(ret.response.InternetServices) == 1

    def test_T5970_with_tag_filter(self):
        indexes, _ = misc.execute_tag_tests(self.a1_r1, 'InternetService', self.is_ids,
                               'oapi.ReadInternetServices', 'InternetServices.InternetServiceId')
        assert indexes == [3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 19, 20, 24, 25, 26, 27, 28, 29]
        known_error('API-399', 'Read calls do not support wildcards in tag filtering')
