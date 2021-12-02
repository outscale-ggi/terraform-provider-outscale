from datetime import datetime, timedelta

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from specs import check_oapi_error
from qa_tina_tools.test_base import OscTinaTest


class Test_ReadConsumptionAccount(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_ReadConsumptionAccount, cls).setup_class()
        cls.start_date = (datetime.utcnow() - timedelta(weeks=20)).isoformat().split('T')[0]
        cls.end_date = (datetime.utcnow() - timedelta(weeks=10)).isoformat().split('T')[0]

    def test_T4763_incorrect_dates(self):
        try:
            self.a1_r1.oapi.ReadConsumptionAccount(ToDate=self.start_date, FromDate=self.end_date)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4118)
