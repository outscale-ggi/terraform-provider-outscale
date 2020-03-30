
import datetime
import pytest

from qa_test_tools.test_base import OscTestSuite, known_error
from qa_test_tools.misc import id_generator
from qa_tina_tools.tools.tina.wait_tools import wait_load_balancer_state
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_find(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_find, cls).setup_class()
        lb_name = id_generator('lbu')
        cls.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                         LoadBalancerName=lb_name, AvailabilityZones=[cls.a1_r1.config.region.az_name])
        wait_load_balancer_state(cls.a1_r1, load_balancer_name_list=[lb_name])
        delete_lbu(cls.a1_r1, lbu_name=lb_name)

    @classmethod
    def teardown_class(cls):
        super(Test_find, cls).teardown_class()

    # test_T000_without_param(self) is not a good idea

    @pytest.mark.region_qa
    def test_T1583_with_limit(self):
        ret = self.a1_r1.intel_lbu.accounting.find(limit=10)
        assert ret.response.result.count == 10
        assert len(ret.response.result.results) == 10
        for result in ret.response.result.results:
            assert result.zone
            assert result.service
            assert isinstance(result.created.dt, datetime.datetime)
            assert hasattr(result, 'closing')
            assert result.tina_acct_id
            assert result.owner
            #assert result.param
            assert result.instance
            assert hasattr(result, 'is_correlated')
            assert hasattr(result, 'is_last')
            assert hasattr(result, 'is_synchronized')
            assert hasattr(result, 'error')
            assert isinstance(result.date.dt, datetime.datetime)
            assert result.operation
            assert result.type
            assert result.id

    @pytest.mark.region_qa
    def test_T1584_with_orders(self):
        try:
            res = self.a1_r1.intel_lbu.accounting.find(limit=3, orders=[('id', 'DESC')]).response.result.results
            assert len(res) == 3
            orig = [i.id for i in res]
            sort = sorted(set(orig), reverse=True)
            for i in range(3):
                assert orig[i] == sort[i]
            pytest.fail('Remove known error code')
        except AssertionError:
            known_error('TINA-4281', 'orders failed with lbu.accounting.find')

        res = self.a1_r1.intel_lbu.accounting.find(limit=3, orders=[('id', 'ASC')]).response.result.results
        orig = [i.id for i in res]
        sort = sorted(orig)
        assert orig == sort
        for i in range(3):
            assert orig[i] == sort[i]

    @pytest.mark.region_qa
    def test_T1585_with_after_id(self):
        ret = self.a1_r1.intel_lbu.accounting.find(limit=1000)
        search_id = ret.response.result.results[ret.response.result.count-4].id
        ret = self.a1_r1.intel_lbu.accounting.find(limit=3, after_id=search_id)
        assert [i.id for i in ret.response.result.results] == [search_id+1, search_id+2, search_id+3]

    @pytest.mark.region_qa
    def test_T1586_with_invalid_after_id(self):
        ret = self.a1_r1.intel_lbu.accounting.find(limit=3, after_id=100000000)
        assert ret.response.result.count == 0
        assert not ret.response.result.results

    def test_T2837_without_force_consistency(self):
        ret = self.a1_r1.intel_lbu.accounting.find(limit=1, orders=[('id', 'DESC')])
        try:
            assert ret.response.result.results[0].date.dt > (datetime.datetime.now() - datetime.timedelta(minutes=2))
        except AssertionError:
            known_error('TINA-4281', 'orders failed with lbu.accounting.find')

    def test_T2838_with_force_consistency(self):
        ret = self.a1_r1.intel_lbu.accounting.find(limit=1, orders=[('id', 'DESC')], force_consistency=True)
        assert ret.response.result.results[0].date.dt < (datetime.datetime.now() - datetime.timedelta(minutes=2))
