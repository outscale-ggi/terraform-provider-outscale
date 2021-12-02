from datetime import datetime, timedelta

import pytest
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest


@pytest.mark.region_admin
class Test_slot_history(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_slot_history, cls).setup_class()
        cls.start_date = (datetime.utcnow() - timedelta(days=10)).isoformat().split('.')[0]
        cls.end_date = datetime.utcnow().isoformat().split('.')[0]

    def test_T5348_without_args(self):
        pytest.skip('Too many data, timeout')
        ret = self.a1_r1.intel.monitor.slot_history()
        assert len(ret.response.result) > 0, 'Could not find any history'

    def test_T5349_only_dates(self):
        ret = self.a1_r1.intel.monitor.slot_history(dt1=self.start_date, dt2=self.end_date)
        assert len(ret.response.result) > 0, 'Could not find any history'

    def test_T5340_server_without_dates(self):
        server_name = self.a1_r1.intel.hardware.get_servers().response.result[0].name
        ret = self.a1_r1.intel.monitor.slot_history(what=server_name)
        assert len(ret.response.result) > 0, 'Could not find any history'

    def test_T5350_server_with_dates(self):
        server_name = self.a1_r1.intel.hardware.get_servers().response.result[0].name
        ret = self.a1_r1.intel.monitor.slot_history(what=server_name, dt1=self.start_date, dt2=self.end_date)
        assert len(ret.response.result) > 0, 'Could not find any history'

    def test_T5351_with_instance(self):
        ret = self.a1_r1.intel.instance.find()
        if not ret.response.result:
            pytest.skip('Could not find any instances.')
        ret = self.a1_r1.intel.monitor.slot_history(what=ret.response.result[0].id)
        assert len(ret.response.result) > 0, 'Could not find any history'

    def test_T5352_with_subnet(self):
        ret = self.a1_r1.intel.subnet.find(alias='private.1')
        if not ret.response.result:
            pytest.skip('Could not find any private subnets.')
        ret = self.a1_r1.intel.monitor.slot_history(what=ret.response.result[0].id)
        assert len(ret.response.result) > 0, 'Could not find any history'

    def test_T5353_with_vgw(self):
        ret = self.a1_r1.intel.vpn.virtual_private_gateway.find()
        if not ret.response.result:
            pytest.skip('Could not find any vgw.')
        vgw_id = None
        for res in ret.response.result:
            tmp_res = self.a1_r1.intel.netimpl.firewall.find_firewalls(filters={'resource': res.id}).response.result
            if len(tmp_res):
                vgw_id = tmp_res[0].vm
                break
        if not vgw_id:
            pytest.skip('Could not find any vgw.')
        ret = self.a1_r1.intel.monitor.slot_history(what=vgw_id)
        assert len(ret.response.result) > 0, 'Could not find any history'

    def test_T5354_with_vpc(self):
        ret = self.a1_r1.intel.vpc.find()
        if not ret.response.result:
            pytest.skip('Could not find any vpc.')
        vpc_id = None
        for res in ret.response.result:
            tmp_res = self.a1_r1.intel.netimpl.firewall.find_firewalls(filters={'resource': res.id}).response.result
            if len(tmp_res):
                vpc_id = tmp_res[0].vm
                break
        if not vpc_id:
            pytest.skip('Could not find any vgw.')
        ret = self.a1_r1.intel.monitor.slot_history(what=vpc_id)
        assert len(ret.response.result) > 0, 'Could not find any history'

    def test_T5355_with_lbu(self):
        ret = self.a1_r1.intel_lbu.lb.describe()
        if not ret.response.result:
            pytest.skip('Could not find any lbu.')
        ret = self.a1_r1.intel.monitor.slot_history(what=ret.response.result[0].name)
        try:
            assert len(ret.response.result) > 0, 'Could not find any history'
            raise OscTestException('Remove known error')
        except AssertionError:
            known_error('TINA-6123', 'No history found for lbus, by name')

    def test_T5443_with_extended_lbu(self):
        ret = self.a1_r1.intel_lbu.lb.describe()
        if not ret.response.result:
            pytest.skip('Could not find any lbu.')
        ret = self.a1_r1.intel.monitor.slot_history(what='lbu-{}'.format(ret.response.result[0].name))
        try:
            assert len(ret.response.result) > 0, 'Could not find any history'
            known_error('TINA-6123', 'No history found for lbus, by name')
        except AssertionError:
            raise OscTestException('Remove known error')

    def test_T5444_with_lbu_wildcard(self):
        ret1 = self.a1_r1.intel.monitor.slot_history(what='lbu*')
        ret2 = self.a1_r1.intel.monitor.slot_history(what='lbu-*')
        assert len(ret2.response.result) > 0, 'Could not find lbu history with wildcard'
        try:
            assert len(ret1.response.result) > 0, 'Could not find any history'
            raise OscTestException('Remove known error')
        except AssertionError:
            known_error('TINA-6123', 'wildcard does not always work')

    def test_T5445_with_vpc_wildcard(self):
        ret1 = self.a1_r1.intel.monitor.slot_history(what='vpc*')
        ret2 = self.a1_r1.intel.monitor.slot_history(what='vpc-*')
        assert len(ret2.response.result) > 0, 'Could not find vpc history with wildcard'
        try:
            assert len(ret1.response.result) > 0, 'Could not find any history'
            raise OscTestException('Remove known error')
        except AssertionError:
            known_error('TINA-6123', 'wildcard does not always work')

    def test_T5446_with_vgw_wildcard(self):
        ret1 = self.a1_r1.intel.monitor.slot_history(what='vgw*')
        ret2 = self.a1_r1.intel.monitor.slot_history(what='vgw-*')
        assert len(ret2.response.result) > 0, 'Could not find vgw history with wildcard'
        try:
            assert len(ret1.response.result) > 0, 'Could not find any history'
            raise OscTestException('Remove known error')
        except AssertionError:
            known_error('TINA-6123', 'wildcard does not always work')

    def test_T5447_with_instance_wildcard(self):
        ret = self.a1_r1.intel.monitor.slot_history(what='i-1*')
        assert len(ret.response.result) > 0, 'Could not find instance history with wildcard'
