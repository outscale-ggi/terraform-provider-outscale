import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_internet_gateways_state


class Test_DeleteInternetService(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteInternetService, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteInternetService, cls).teardown_class()

    def test_T2240_valid_params(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId
            wait_internet_gateways_state(self.a1_r1, [net_id], state='available')
            self.a1_r1.oapi.DeleteInternetService(InternetServiceId=net_id)
            net_id = None
        finally:
            if net_id:
                try:
                    self.a1_r1.oapi.DeleteInternetService(InternetServiceId=net_id)
                except:
                    print('Could not delete internet service')

    def test_T2241_valid_params_dry_run(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId
            wait_internet_gateways_state(self.a1_r1, [net_id], state='available')
            ret = self.a1_r1.oapi.DeleteInternetService(InternetServiceId=net_id, DryRun=True)
            assert_dry_run(ret)
        finally:
            if net_id:
                try:
                    self.a1_r1.oapi.DeleteInternetService(InternetServiceId=net_id)
                except:
                    print('Could not delete internet service')

    def test_T3459_without_params(self):
        try:
            self.a1_r1.oapi.DeleteInternetService()
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'MissingParameter', '7000')

    @pytest.mark.tag_sec_confidentiality
    def test_T3460_valid_params_other_account(self):
        try:
            net_id = self.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId
            wait_internet_gateways_state(self.a1_r1, [net_id], state='available')
            self.a2_r1.oapi.DeleteInternetService(InternetServiceId=net_id)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidResource', '5001')
        finally:
            if net_id:
                try:
                    self.a1_r1.oapi.DeleteInternetService(InternetServiceId=net_id)
                except:
                    print('Could not delete internet service')

    def test_T3815_invalid_internet_service_id(self):
        try:
            self.a1_r1.oapi.DeleteInternetService(InternetServiceId='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4104')

    def test_T3816_deleted_internet_service(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId
            wait_internet_gateways_state(self.a1_r1, [net_id], state='available')
            self.a1_r1.oapi.DeleteInternetService(InternetServiceId=net_id)
            self.a1_r1.oapi.DeleteInternetService(InternetServiceId=net_id)
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidResource', '5001')
