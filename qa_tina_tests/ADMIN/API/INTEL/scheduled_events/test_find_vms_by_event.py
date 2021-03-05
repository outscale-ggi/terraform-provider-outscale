from datetime import datetime, timedelta

import pytz

from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


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
        kvm_selected = None
        start_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
            days=1)
        end_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            days=2)
        hardware_groups = self.a1_r1.intel.hardware.get_account_bindings(account=self.a1_r1.config.account.account_id). \
            response.result
        ret = self.a1_r1.intel.slot.find_server_resources(min_core=15, min_memory=15 * pow(1024, 3), pz='in2',
                                                          hw_groups=hardware_groups)
        for server in ret.response.result:
            if server.state == 'READY':
                kvm_selected = server.name
                break
        event_id = None
        try:
            ret_event = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change', resource_type='server',
                                                     targets=[kvm_selected], start_date=str(start_date), end_date=str(end_date),
                                                     description='test')
            event_id = ret_event.response.result.id
            # ret = self.a1_r1.intel.scheduled_events.find()
            # event_id = ret.response.result[0].id
            ret = self.a1_r1.intel.scheduled_events.find_vms_by_event(event_id=event_id)
            assert len(ret.response.result) > 0
        finally:
            if event_id:
                self.a1_r1.intel.scheduled_events.finish(event_id=event_id)
