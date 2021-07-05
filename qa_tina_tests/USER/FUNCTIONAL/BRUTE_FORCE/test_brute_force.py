import time


import pytest


from qa_sdk_pub import osc_api
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdks import OscSdk

from qa_test_tools.config import config_constants as constants, OscConfig
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from specs import check_oapi_error


@pytest.mark.region_admin
class Test_brute_force(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_brute_force, cls).setup_class()
        cls.a1_r1.identauth.IdauthAccount.putAccountBruteForceProtectionPolicy(
            bruteForceProtectionPolicy={"attemptThreshold": 5, "trialPeriodSec": 60, "banCooldownSec": 60})
        cls.a1_r1.identauth__admin.IdauthAdmin.invalidateCache(
            account_id=cls.a1_r1.config.region.get_info(constants.AS_IDAUTH_ID))

    @classmethod
    def teardown_class(cls):
        cls.a1_r1.identauth.IdauthAccount.deleteAccountBruteForceProtectionPolicy()
        cls.a1_r1.identauth__admin.IdauthAdmin.invalidateCache(
            account_id=cls.a1_r1.config.region.get_info(constants.AS_IDAUTH_ID))
        super(Test_brute_force, cls).teardown_class()

    def test_T5644_ak_sk(self):
        # access_key = None
        ret_create = self.a1_r1.oapi.CreateAccessKey()
        access_key = ret_create.response.AccessKey.AccessKeyId
        secret_key = ret_create.response.AccessKey.SecretKey
        account_sdk = OscSdk(config=OscConfig.get_with_keys(
            az_name=self.a1_r1.config.region.az_name,
            ak=access_key,
            sk=secret_key))
        account_sdk.lbu.DescribeLoadBalancers(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
        wrong_account_sdk = OscSdk(config=OscConfig.get_with_keys(
            az_name=self.a1_r1.config.region.az_name,
            ak=access_key,
            sk=secret_key + "AB"))
        try:

            for i in range(6):
                try:
                    wrong_account_sdk.oapi.ReadVms(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                    time.sleep(2)
                except OscApiException as error:
                    check_oapi_error(error, 1)
                    print(i)
                    print(error)
            try:
                time.sleep(2)
                ret = wrong_account_sdk.oapi.ReadVms(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                check_oapi_error(error, 13)
            try:
                time.sleep(2)
                ret = account_sdk.oapi.ReadVms(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                check_oapi_error(error, 13)
            time.sleep(2)
            self.a1_r1.oapi.ReadVms(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
            dict_services = {'eim': 'ListUsers', 'directlink': 'DescribeLocations', 'fcu': 'DescribeVolumes',
                             'icu': 'ListAccessKeys', 'lbu': 'DescribeLoadBalancers'}
            for service, call in dict_services.items():
                try:
                    connector = getattr(account_sdk, service)
                    getattr(connector, call)(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                    assert False, 'Call should not have been successful'
                except OscApiException as error:
                    assert_error(error, 401, 'AuthFailure', 'Outscale was not able to validate the provided access '
                                                            'credentials. Invalid login/password or password has expired.')
        except Exception as error:
            raise error
        finally:
            if access_key:
                self.a1_r1.oapi.DeleteAccessKey(AccessKeyId=access_key)

    def test_T5645_login_password(self):
        for i in range(6):
            try:
                self.a1_r1.icu.ListAccessKeys(
                    exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                               osc_api.EXEC_DATA_PASSWORD: 'toto'})
                time.sleep(2)
            except OscApiException as error:
                assert_error(error, 403, 'InvalidLoginPassword', 'Account {} failed to authenticate.'.format(self.a1_r1.config.account.login))
                print(i)
                print(error)
        try:
            time.sleep(2)
            self.a1_r1.icu.ListAccessKeys(
                exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                           osc_api.EXEC_DATA_PASSWORD: 'toto'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 401, 'AuthFailure', 'Outscale was not able to validate the provided access '
                                                    'credentials. Invalid login/password or password has expired.')
            print(error)
        try:
            time.sleep(2)
            self.a1_r1.icu.ListAccessKeys(
                exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 401, 'AuthFailure', 'Outscale was not able to validate the provided access '
                                                    'credentials. Invalid login/password or password has expired.')
            print(error)
        try:
            self.a1_r1.oapi.ReadAccessKeys(
                exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 13)
