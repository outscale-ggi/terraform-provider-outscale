from datetime import datetime, timedelta

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.test_base import OscTestSuite


class Test_ReadConsumptionAccount(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadConsumptionAccount, cls).setup_class()
        cls.start_date = (datetime.utcnow() - timedelta(weeks=20)).isoformat().split('T')[0]
        cls.end_date = (datetime.utcnow() - timedelta(weeks=10)).isoformat().split('T')[0]
        try:
            pass
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_ReadConsumptionAccount, cls).teardown_class()

    def test_T4762_correct_dates(self):
        ret = self.a1_r1.oapi.ReadConsumptionAccount(FromDate=self.start_date, ToDate=self.end_date)
        assert ret.response.ConsumptionEntries
        ret.check_response()

    def test_T4763_incorrect_dates(self):
        try:
            self.a1_r1.oapi.ReadConsumptionAccount(ToDate=self.start_date, FromDate=self.end_date)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', '4118')
