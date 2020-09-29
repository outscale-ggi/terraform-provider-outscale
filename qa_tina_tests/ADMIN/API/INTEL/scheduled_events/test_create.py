# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

import datetime
import re

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_create(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create, cls).setup_class()
        try:
            cls.events = []
            cls.start_date = (datetime.datetime.now()+datetime.timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
            cls.end_date = (datetime.datetime.now()+datetime.timedelta(days=20)).strftime("%Y-%m-%d %H:%M:%S")
            # TODO: update for others regions
            if cls.a1_r1.config.region.name == "in-west-2":
                cls.kvm = 'in2-ucs1-pr-kvm-12'
                cls.types = {'hardware-change': {'cluster': ['1'],      # 1 --> 'ucs1'
                                                 'server': ['in2-ucs1-pr-kvm-12'],
                                                 #'dl_router': [''],    # No capa
                                                },
                             'software-upgrade': {'cluster': ['1'],     # 1 --> 'ucs1'
                                                  'server': ['in2-ucs1-pr-kvm-12'],
                                                 },
                             'software-maintenance': {'pz': ['in2'],
                                                      #'load_balancer': [''], # TINA-3817: Not implemented
                                                      'subnet': ['subnet-7cc17fdf'],
                                                      'storage_shard': ['4'],     # 4 --> '/vm'
                                                     },
                            }
            else:
                cls.kvm = 'in1-ucs1-23-kvm-1'
                cls.types = {'hardware-change': {'cluster': ['1'],      # 1 --> 'ucs1'
                                                 'server': ['in1-ucs1-23-kvm-1'],
                                                 #'dl_router': [''],    # No capa
                                                },
                             'software-upgrade': {'cluster': ['1'],     # 1 --> 'ucs1'
                                                  'server': ['in1-ucs1-23-kvm-1'],
                                                 },
                             'software-maintenance': {'pz': ['in1'],
                                                      #'load_balancer': [''], # TINA-3817: Not implemented
                                                      'subnet': ['subnet-dd9975dc'],
                                                      'storage_shard': ['9'],     # 4 --> '/vm'
                                                     },
                            }
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
            super(Test_create, cls).teardown_class()

    def setup_method(self, method):
        super(Test_create, self).setup_method(method)
        self.events = []

    def teardown_method(self, method):
        try:
            for event in self.events:
                self.a1_r1.intel.scheduled_events.finish(event_id=event)
        finally:
            super(Test_create, self).teardown_method(method)

    def test_T2543_required_param(self):
        ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                       resource_type='server',
                                                       targets=[self.kvm],
                                                       start_date=self.start_date,
                                                       end_date=self.end_date
                                                       )
        self.events.append(ret.response.result.id)
        assert ret.response.result.status == 'planned'
        assert not ret.response.result.auto_actions
        assert ret.response.result.event_type == 'hardware-change'
        assert ret.response.result.end_date == self.end_date
        assert ret.response.result.start_date == self.start_date
        assert not ret.response.result.description
        assert re.search(r"(event-[a-zA-Z0-9]{8})", ret.response.result.id)
        assert ret.response.result.resource_type == 'server'
        assert ret.response.result.target[0] == self.kvm

    def test_T2544_with_valid_types(self):
        for event, info in self.types.items():
            for resource, targets in info.items():
                ret = self.a1_r1.intel.scheduled_events.create(event_type=event,
                                                               resource_type=resource,
                                                               targets=targets,
                                                               start_date=self.start_date,
                                                               end_date=self.end_date
                                                               )
                self.a1_r1.intel.scheduled_events.finish(event_id=ret.response.result.id)
                # self.events.append(ret.response.result.id)

    def test_T2545_without_event_type(self):
        try:
            ret = self.a1_r1.intel.scheduled_events.create(resource_type='server',
                                                           targets=[self.kvm],
                                                           start_date=self.start_date,
                                                           end_date=self.end_date
                                                           )
            self.events.append(ret.response.result.id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message == 'Internal error.':
                known_error('TINA-4684', 'Unexpected internal error')
            assert False, "Remove known error"
            assert_error(error, 400, 'MissingParam', '...')

    def test_T2546_without_resource_type(self):
        try:
            ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                           targets=[self.kvm],
                                                           start_date=self.start_date,
                                                           end_date=self.end_date
                                                           )
            self.events.append(ret.response.result.id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message == 'Internal error.':
                known_error('TINA-4684', 'Unexpected internal error')
            assert False, "Remove known error"
            assert_error(error, 400, 'MissingParam', '...')

    def test_T2547_without_targets(self):
        try:
            ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                           resource_type='server',
                                                           start_date=self.start_date,
                                                           end_date=self.end_date
                                                           )
            self.events.append(ret.response.result.id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message == 'Internal error.':
                known_error('TINA-4684', 'Unexpected internal error')
            assert False, "Remove known error"
            assert_error(error, 400, 'MissingParam', '...')

    def test_T2548_without_start_date(self):
        try:
            ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                           resource_type='server',
                                                           targets=[self.kvm],
                                                           end_date=self.end_date
                                                           )
            self.events.append(ret.response.result.id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message == 'Internal error.':
                known_error('TINA-4684', 'Unexpected internal error')
            assert False, "Remove known error"
            assert_error(error, 400, 'MissingParam', '...')

    def test_T2549_without_end_date(self):
        try:
            ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                           resource_type='server',
                                                           targets=[self.kvm],
                                                           start_date=self.start_date
                                                           )
            self.events.append(ret.response.result.id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message == 'Internal error.':
                known_error('TINA-4684', 'Unexpected internal error')
            assert False, "Remove known error"
            assert_error(error, 400, 'MissingParam', '...')

    def test_T2550_with_description(self):
        ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                       resource_type='server',
                                                       targets=[self.kvm],
                                                       start_date=self.start_date,
                                                       end_date=self.end_date,
                                                       description='event description'
                                                       )
        self.events.append(ret.response.result.id)
        assert ret.response.result.description == 'event description'

    def test_T2551_with_auto_actions(self):
        ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                       resource_type='server',
                                                       targets=[self.kvm],
                                                       start_date=self.start_date,
                                                       end_date=self.end_date,
                                                       auto_actions=True
                                                       )
        self.events.append(ret.response.result.id)
        assert ret.response.result.auto_actions

    def test_T2552_with_invalid_event_type(self):
        try:
            ret = self.a1_r1.intel.scheduled_events.create(event_type='foo',
                                                           resource_type='server',
                                                           targets=[self.kvm],
                                                           start_date=self.start_date,
                                                           end_date=self.end_date
                                                           )
            self.events.append(ret.response.result.id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'wrong-event-type')

    def test_T2553_with_invalid_resource_type(self):
        try:
            ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                           resource_type='foo',
                                                           targets=[self.kvm],
                                                           start_date=self.start_date,
                                                           end_date=self.end_date
                                                           )
            self.events.append(ret.response.result.id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'wrong-resource-type')

    def test_T2554_with_invalid_targets(self):
        try:
            ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                           resource_type='server',
                                                           targets=['foo'],
                                                           start_date=self.start_date,
                                                           end_date=self.end_date
                                                           )
            self.events.append(ret.response.result.id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'no-such-target')

    def test_T2555_with_invalid_start_date(self):
        try:
            ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                           resource_type='server',
                                                           targets=[self.kvm],
                                                           start_date='foo',
                                                           end_date=self.end_date
                                                           )
            self.events.append(ret.response.result.id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'impossible-date-conversion')

    def test_T2556_with_invalid_end_date(self):
        try:
            ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                           resource_type='server',
                                                           targets=[self.kvm],
                                                           start_date=self.start_date,
                                                           end_date='foo'
                                                           )
            self.events.append(ret.response.result.id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'impossible-date-conversion')

    def test_T2557_with_invalid_auto_actions(self):
        try:
            ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                           resource_type='server',
                                                           targets=[self.kvm],
                                                           start_date=self.start_date,
                                                           end_date=self.end_date,
                                                           auto_actions='foo'
                                                           )
            self.events.append(ret.response.result.id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message == 'Internal error.':
                known_error('TINA-4684', 'Unexpected internal error')
            assert False, "Remove known error"
            assert_error(error, 200, 0, 'invalid auto_actions')

    def test_T2558_with_end_before_start(self):
        try:
            ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                           resource_type='server',
                                                           targets=[self.kvm],
                                                           start_date=self.end_date,
                                                           end_date=self.start_date
                                                           )
            self.events.append(ret.response.result.id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'wrong-date')

    # def test_T0000_with_dates_in_past(self): --> expected ???
    #    try:
    #        start_date = (datetime.datetime.now()-datetime.timedelta(days=20)).strftime("%Y-%m-%d %H:%M:%S")
    #        end_date = (datetime.datetime.now()-datetime.timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
    #        ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
    #                                                       resource_type='server',
    #                                                       targets=[self.kvm],
    #                                                       start_date=start_date,
    #                                                       end_date=end_date
    #                                                      )
    #        self.events.append(ret.response.result.id)
    #        assert False, 'Call should not have been successful'
    #    except OscApiException as error:
    #        assert_error(error, 200, 0, 'wrong-date')

    def test_T2559_with_same_dates(self):
        try:
            ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                           resource_type='server',
                                                           targets=[self.kvm],
                                                           start_date=self.start_date,
                                                           end_date=self.end_date
                                                           )
            self.events.append(ret.response.result.id)
            ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                           resource_type='server',
                                                           targets=[self.kvm],
                                                           start_date=self.start_date,
                                                           end_date=self.end_date
                                                           )
            self.events.append(ret.response.result.id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'overlapping-timespan')

    def test_T5128_with_overlapping_event(self):
        ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                       resource_type='server',
                                                       targets=[self.kvm],
                                                       start_date=self.start_date,
                                                       end_date=self.end_date
                                                       )
        self.events.append(ret.response.result.id)

        events = ((5,25), (5, 15), (15, 25), (12, 18))
        for i,j in events:
            try:
                ret = self.a1_r1.intel.scheduled_events.create(event_type='hardware-change',
                                                               resource_type='server',
                                                               targets=[self.kvm],
                                                               start_date=(datetime.datetime.now() + datetime.timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S"),
                                                               end_date=(datetime.datetime.now() + datetime.timedelta(days=j)).strftime("%Y-%m-%d %H:%M:%S")
                                                               )
                self.events.append(ret.response.result.id)
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 200, 0, 'overlapping-timespan')
