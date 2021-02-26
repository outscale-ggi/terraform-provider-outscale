import datetime
import time

import pytest

from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_volumes

VOLUME_DELETION_PERIOD = 30


@pytest.mark.region_admin
class Test_volume(OscTestSuite):
    @classmethod
    def setup_class(cls):
        super(Test_volume, cls).setup_class()
        try:
            cls.account_id = cls.a1_r1.config.account.account_id
            cls.account2_id = cls.a2_r1.config.account.account_id
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception as err:
                raise err
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_volume, cls).teardown_class()

    def test_T4153_deletion_process(self):
        # TODO get period via consul, for now global variable
        period = VOLUME_DELETION_PERIOD
        vol_id = None
        try:
            _, [vol_id] = create_volumes(self.a1_r1, count=1, state='available')
            start = datetime.datetime.utcnow()
            self.a1_r1.fcu.DeleteVolume(VolumeId=vol_id)
            ret = 1
            while ret and datetime.datetime.utcnow() - start < datetime.timedelta(seconds=period * 2):
                ret = self.a1_r1.intel.volume.find(id=vol_id).response.result
                time.sleep(1)
            vol_id = None
            if ret:
                raise OscTestException("Volume was not erased in time")
        finally:
            if vol_id:
                self.a1_r1.fcu.DeleteVolume(VolumeId=vol_id)
