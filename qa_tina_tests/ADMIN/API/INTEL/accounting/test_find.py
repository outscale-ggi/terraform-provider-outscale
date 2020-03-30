# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

import datetime
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_volumes

ACCOUNTING_GRACE_TIME = 2


class Test_find(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_find, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_find, cls).teardown_class()

    # test_T000_without_param(self) is not a good idea

    def test_T1579_with_limit(self):
        ret = self.a1_r1.intel.accounting.find(limit=10, orders=[('id', 'DESC')])
        assert ret.response.result.count == 10
        assert len(ret.response.result.results) == 10
        for result in ret.response.result.results:
            assert hasattr(result, 'zone')
            assert hasattr(result, 'service')
            assert isinstance(result.created.dt, datetime.datetime)
            assert hasattr(result, 'closing')
            assert hasattr(result, 'tina_acct_id')
            assert hasattr(result, 'owner')
            assert hasattr(result, 'param')
            assert hasattr(result, 'instance')
            assert hasattr(result, 'is_correlated')
            assert hasattr(result, 'is_last')
            assert hasattr(result, 'is_synchronized')
            assert hasattr(result, 'error')
            assert isinstance(result.date.dt, datetime.datetime)
            assert hasattr(result, 'operation')
            assert hasattr(result, 'type')
            assert hasattr(result, 'id')

    def test_T1580_with_orders(self):
        res = self.a1_r1.intel.accounting.find(limit=3, orders=[('id', 'DESC')]).response.result.results
        assert len(res) == 3
        orig = [i.id for i in res]
        sort = sorted(set(orig), reverse=True)
        for i in range(3):
            assert orig[i] == sort[i]

        res = self.a1_r1.intel.accounting.find(limit=3, orders=[('id', 'ASC')]).response.result.results
        orig = [i.id for i in res]
        sort = sorted(orig)
        assert orig == sort
        for i in range(3):
            assert orig[i] == sort[i]

    def test_T1581_with_after_id(self):
        ret = self.a1_r1.intel.accounting.find(limit=3, after_id=10000)
        for i in ret.response.result.results:
            assert i.id > 10000

    def test_T1582_with_invalid_after_id(self):
        ret = self.a1_r1.intel.accounting.find(limit=3, after_id=100000000)
        assert ret.response.result.count == 0
        assert not ret.response.result.results

    def test_T2835_without_force_consistency(self):
        vol_id_list = None
        try:
            _, vol_id_list = create_volumes(self.a1_r1)
            ret = self.a1_r1.intel.accounting.find(limit=1, orders=[('id', 'DESC')])
            assert ret.response.result.results[0].date.dt > (datetime.datetime.utcnow() - datetime.timedelta(minutes=ACCOUNTING_GRACE_TIME))
        finally:
            if vol_id_list:
                delete_volumes(self.a1_r1, vol_id_list)

    def test_T2836_with_force_consistency(self):
        vol_id_list = None
        try:
            _, vol_id_list = create_volumes(self.a1_r1)
            ret = self.a1_r1.intel.accounting.find(limit=1, orders=[('id', 'DESC')], force_consistency=True)
            assert ret.response.result.results[0].date.dt < (datetime.datetime.utcnow() - datetime.timedelta(minutes=ACCOUNTING_GRACE_TIME))
        finally:
            if vol_id_list:
                delete_volumes(self.a1_r1, vol_id_list)

    # Unable to reproduce BILLING issue !!!
#    def test_T0000_stress(self):
#
#        def exec_job(osc_sdk, nb_retry):
#            inst_info = None
#            try:
#                inst_info = create_instances(osc_sdk=osc_sdk, inst_type='t2.nano', state='running')
#                for i in range(nb_retry):
#                    osc_sdk.fcu.StopInstances(InstanceId=inst_info[INSTANCE_ID_LIST], Force=True)
#                    wait_instances_state(osc_sdk=osc_sdk, instance_id_list=inst_info[INSTANCE_ID_LIST], state='stopped')
#                    osc_sdk.fcu.StartInstances(InstanceId=inst_info[INSTANCE_ID_LIST])
#                    wait_instances_state(osc_sdk=osc_sdk, instance_id_list=inst_info[INSTANCE_ID_LIST], state='running')
#            finally:
#                if inst_info:
#                    delete_instances(osc_sdk, inst_info)
#
#        nb_worker = 20
#        nb_retry = 15
#
#        threads = []
#
#        for i in range(nb_worker):
#            t = Process(target=exec_job,
#                        args=(self.a1_r1, nb_retry))
#            threads.append(t)
#
#        ret = self.a1_r1.intel.accounting.find(limit=1, orders=[('id', 'DESC')])
#        last_id = ret.response.result.results[0].tina_acct_id
#
#        for i in range(len(threads)):
#            threads[i].start()
#
#        missing_id = {}
#        found_id = {}
#        alive = True
#
#        # Loop until Process are running
#        while alive:
#
#            # New request execution
#            #time.sleep(1)
#            ret = self.a1_r1.intel.accounting.find(limit=5000, orders=[('id', 'ASC')], after_id=last_id-1)
#
#            # check if some missing ids are found with the last request
#            for i in missing_id.keys():
#                if i in [r.tina_acct_id for r in ret.response.result.results]:
#                    found_id[i] = (missing_id[i], [r.tina_acct_id for r in ret.response.result.results])
#                    del missing_id[i]
#
#            # check request response and update last_id
#            prev_id = last_id
#            for r in ret.response.result.results:
#                if r.tina_acct_id == last_id:
#                    last_id += 1
#                elif r.tina_acct_id != prev_id and prev_id not in missing_id.key():
#                        missing_id[prev_id] = [i.tina_acct_id for i in ret.response.result.results]
#                    #break
#                prev_id +=1
#
#            # Check process states
#            for i in range(len(threads)):
#                if threads[i].is_alive():
#                    break
#                alive = False
#
#        for i in missing_id.keys():
#            print("Id '{}' not found in {}".format(i, missing_id[i]))
#
#        for i in found_id.keys():
#            print("Id '{}' not found in {} but found in {}".format(i, found_id[i][0], found_id[i][1]))
#
#        for i in range(len(threads)):
#            threads[i].join()
