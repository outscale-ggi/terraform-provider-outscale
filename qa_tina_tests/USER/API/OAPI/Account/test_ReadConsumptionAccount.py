from datetime import datetime, timedelta

import pytz
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.specs.check_tools import check_oapi_response
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc



class Test_ReadConsumptionAccount(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadConsumptionAccount, cls).setup_class()
        cls.start_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=10)
        try:
            pass
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_ReadConsumptionAccount, cls).teardown_class()

    def test_T4762_correct_dates(self):
        end_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=3)
        ret = self.a1_r1.oapi.ReadConsumptionAccount(FromDate=self.start_date.isoformat(), ToDate=end_date.isoformat())
        check_oapi_response(ret.response, 'ReadConsumptionAccountResponse')

    def test_T4763_incorrect_dates(self):
        end_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=3)
        try:
            self.a1_r1.oapi.ReadConsumptionAccount(ToDate=self.start_date.isoformat(), FromDate=end_date.isoformat())
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', '4118')
