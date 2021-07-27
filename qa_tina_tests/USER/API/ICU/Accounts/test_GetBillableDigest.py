from datetime import datetime, timedelta

import pytest
import pytz

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
from qa_test_tools.misc import assert_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools import constants


@pytest.mark.region_getbillabledigest
class Test_GetBillableDigest(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_GetBillableDigest, cls).setup_class()
        cls.start_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30)
        try:
            cls.gbd_oscsdk = OscSdk(config=OscConfig.get(az_name=cls.a1_r1.config.region.az_name, account_name=constants.GBD_KEY))
        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    def test_T1681_correct_dates(self):
        end_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=10)
        try:
            self.gbd_oscsdk.icu.GetBillableDigest(owner=self.a1_r1.config.account.account_id,
                                                  fromDate=self.start_date.isoformat(), toDate=end_date.isoformat(), invoiceType='CURRENT')
        except OscApiException as error:
            if error.message != 'The information for requested dates is not yet available.':
                raise error

    def test_T1682_incorrect_dates(self):
        end_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=10)
        try:
            self.gbd_oscsdk.icu.GetBillableDigest(owner=self.a1_r1.config.account.account_id,
                                                  toDate=self.start_date.isoformat(), fromDate=end_date.isoformat(), invoiceType='CURRENT')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Value for 'fromDate' must be less than value for 'toDate'.")

    def test_T5755_with_extra_param(self):
        end_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=10)
        try:
            self.gbd_oscsdk.icu.GetBillableDigest(owner=self.a1_r1.config.account.account_id, Foo='Bar',
                                                  fromDate=self.start_date.isoformat(), toDate=end_date.isoformat(), invoiceType='CURRENT')
        except OscApiException as error:
            if error.message != 'The information for requested dates is not yet available.':
                raise error
