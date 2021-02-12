import datetime

from time import sleep

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_ListAccessKeys(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ListAccessKeys, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ListAccessKeys, cls).teardown_class()

    def test_T1495_without_param(self):
        ret = self.a1_r1.icu.ListAccessKeys()
        assert len(ret.response.accessKeys) >= 1
        # TODO: check returned attributes

    # TODO: add more tests

    def test_T5265_check_expiration_date(self):
        sleep(11)
        try:
            ak_id = None
            exp_date_found = False
            today = datetime.date.today()
            exp_year = today.year
            exp_month = today.month + 1
            if today.month == 12:
                exp_month = 1
                exp_year += 1
            expiration_date = datetime.date(exp_year, exp_month, 28)
            expiration_date = expiration_date.strftime("%Y-%m-%d")
            ret = self.a1_r1.oapi.CreateAccessKey(ExpirationDate=expiration_date)
            ak_id = ret.response.AccessKey.AccessKeyId
            ret = self.a1_r1.icu.ListAccessKeys()
            assert len(ret.response.accessKeys) >= 1
            for ak in ret.response.accessKeys:
                if ak.accessKeyId == ak_id:
                    assert expiration_date in ak.expirationDate
                    exp_date_found = True
                    break
            if not exp_date_found:
                assert False, "response should contain a not null expirationDate "
        finally:
            if ak_id:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak_id)
    def test_T3775_check_throttling(self):
        sleep(11)
        found_error = False
        osc_api.disable_throttling()
        self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
        for _ in range(3):
            try:
                self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
            except OscApiException as error:
                if error.status_code == 503:
                    found_error = True
                else:
                    raise error
        osc_api.enable_throttling()
        assert found_error, "Throttling did not happen"

    def test_T3968_non_authenticated(self):
        sleep(11)
        try:
            self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'IcuClientException', 'Field AuthenticationMethod is required')

    def test_T3978_with_method_ak_sk(self):
        sleep(11)
        ret = self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk})
        assert len(ret.response.accessKeys) >= 1
        # TODO: check returned attributes

    def test_T3979_with_method_login_password(self):
        sleep(11)
        ret = self.a1_r1.icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword})
        assert len(ret.response.accessKeys) >= 1
        # TODO: check returned attributes
