import pytest

from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.misc import assert_dry_run, assert_oapi_error
from osc_common.exceptions.osc_exceptions import OscApiException

NUM_INTERNET_SERVICES = 3


class Test_ReadInternetServices(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadInternetServices, cls).setup_class()
        cls.net_ids = []
        try:
            for i in range(NUM_INTERNET_SERVICES):
                net_id = cls.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId
                cls.net_ids.append(net_id)
                cls.a1_r1.oapi.CreateTags(ResourceIds=[net_id], Tags=[{'Key': 'key' + str(i), 'Value': 'value' + str(i)}])
            pass
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            for net_id in cls.net_ids:
                cls.a1_r1.oapi.DeleteInternetService(InternetServiceId=net_id)
        finally:
            super(Test_ReadInternetServices, cls).teardown_class()

    def test_T2242_valid_params(self):
        self.a1_r1.oapi.ReadInternetServices()

    def test_T2243_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadInternetServices(DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3429_other_account(self):
        ret = self.a2_r1.oapi.ReadInternetServices().response.InternetServices
        assert not ret

    @pytest.mark.tag_sec_confidentiality
    def test_T3430_other_account_with_filter(self):
        ret = self.a2_r1.oapi.ReadInternetServices(Filters={'InternetServiceIds': self.net_ids}).response.InternetServices
        assert not ret

    def test_T3824_with_tags_filter(self):
        ret = self.a1_r1.oapi.ReadInternetServices(Filters={'Tags': ['key0=value0']})
        assert len(ret.response.InternetServices) == 1

    def test_T3825_with_tags_keys_filter(self):
        ret = self.a1_r1.oapi.ReadInternetServices(Filters={'TagKeys': ['key0']})
        assert len(ret.response.InternetServices) == 1

    def test_T3826_with_tag_values_filter(self):
        ret = self.a1_r1.oapi.ReadInternetServices(Filters={'TagValues': ['value0']})
        assert len(ret.response.InternetServices) == 1

    def test_T3827_with_internet_service_ids_filter(self):
        ret = self.a1_r1.oapi.ReadInternetServices(Filters={'InternetServiceIds': [self.net_ids[0]]})
        assert len(ret.response.InternetServices) == 1

    def test_T3828_multi_internet_service_no_capa(self):
        try:
            for _ in range(6):
                self.net_ids.append(self.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId)
        except OscApiException as err:
            assert_oapi_error(err, 400, 'TooManyResources (QuotaExceded)', '10023')
