import base64
import sys

import pytest

from qa_common_tools import constants
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.delete_tools import terminate_instances
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


def evaluate_server(server):
    return server.available_core * 10 + server.available_memory // pow(1024, 3)


class Test_min_max_behavior(OscTestSuite):
    @classmethod
    def setup_class(cls):
        super(Test_min_max_behavior, cls).setup_class()
        try:
            pass
        except Exception as error:
            cls.teardown_class()
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_min_max_behavior, cls).teardown_class()

    @pytest.mark.region_admin
    def test_T4517_min_max_count_behavior(self):
        hardware_groups = self.a1_r1.intel.hardware.get_account_bindings(account=self.a1_r1.config.account.account_id).\
            response.result
        best_eval = sys.maxsize
        kvm_selected = None
        ret = self.a1_r1.intel.slot.find_server_resources(min_core=15, min_memory=15 * pow(1024, 3), pz='in2',
                                                          hw_groups=hardware_groups)
        for server in ret.response.result:
            if server.state != 'READY':
                continue
            if not hasattr(server.tags, 'instancetype'):
                continue
            if '*' not in server.tags.instancetype.split(','):
                continue
            current_eval = evaluate_server(server)
            if current_eval < best_eval:
                kvm_selected = server
                best_eval = current_eval
        userdata = """-----BEGIN OUTSCALE SECTION-----
                   pin={}
                   -----END OUTSCALE SECTION-----""".format(kvm_selected.name)
        userdata = base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
        if kvm_selected:
            inst_ids = None
            try:
                core_per_inst = int(kvm_selected.available_core//10)
                ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region._conf[constants.CENTOS7], MaxCount=20,
                                                  MinCount=5,
                                                  InstanceType='tinav3.c{}r1'.format(core_per_inst),
                                                  UserData=userdata)
                inst_ids = [inst.instanceId for inst in ret.response.instancesSet]
                assert len(inst_ids) == int(kvm_selected.available_core / core_per_inst)
                wait_instances_state(self.a1_r1, inst_ids, state='running')
                ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, state='running')
                kvms = set([inst.servers[0].server for inst in ret.response.result])
                assert len(kvms) == 1 and kvms.pop() == kvm_selected.name
            finally:
                if inst_ids:
                    terminate_instances(self.a1_r1, inst_ids)
