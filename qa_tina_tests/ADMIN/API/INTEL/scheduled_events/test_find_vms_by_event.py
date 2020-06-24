from datetime import datetime, timedelta
from qa_test_tools.test_base import OscTestSuite
import pytz


class Test_find_vms_by_event(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_find_vms_by_event, cls).setup_class()
        try:
            cls.events = []

        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            cls.a1_r1.intel.scheduled_events.gc()
        finally:
            super(Test_find_vms_by_event, cls).teardown_class()


    def test_T210_with_correct_params(self):
        start_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
            days=1)
        end_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            days=2)
        PINKVM = 'in2-ucs1-pr-kvm-2'
        ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change', resource_type='server',
                                                       targets=[PINKVM], start_date=str(start_date), end_date=str(end_date),
                                                       description='test')
        ret = self.a1_r1.intel.scheduled_events.find()
        event_id = ret.response.result[0].id
        ret = self.a1_r1.intel.scheduled_events.find_vms_by_event(event_id=event_id)
        assert len(ret.response.result) > 0
        self.a1_r1.intel.scheduled_events.finish(event_id=event_id)
