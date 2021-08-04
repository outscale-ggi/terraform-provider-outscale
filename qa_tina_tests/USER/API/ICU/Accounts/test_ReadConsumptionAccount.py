from datetime import datetime, timedelta

import pytz

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_tina_tools.test_base import OscTinaTest


class Test_ReadConsumptionAccount(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_ReadConsumptionAccount, cls).setup_class()
        cls.start_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=10)

    def test_T1613_correct_dates(self):
        end_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=3)
        try:
            self.a1_r1.icu.ReadConsumptionAccount(FromDate=self.start_date.isoformat(), ToDate=end_date.isoformat())
        except OscApiException as error:
            if error.status_code == 400 and error.error_code == 'InvalidParameter' and \
                    error.message == 'The information for requested dates is not yet available.':
                return
            raise error

    def test_T1614_incorrect_dates(self):
        end_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=3)
        try:
            self.a1_r1.icu.ReadConsumptionAccount(ToDate=self.start_date.isoformat(), FromDate=end_date.isoformat())
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Value for 'fromDate' must be less than value for 'toDate'.")

    def test_T5756_with_extra_param(self):
        end_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=3)
        try:
            self.a1_r1.icu.ReadConsumptionAccount(FromDate=self.start_date.isoformat(), ToDate=end_date.isoformat(), Foo='Bar')
        except OscApiException as error:
            if error.status_code == 400 and error.error_code == 'InvalidParameter' and \
                    error.message == 'The information for requested dates is not yet available.':
                return
            raise error
