import base64
import pytest

from qa_test_tools.exceptions import OscTestException
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import stop_instances, delete_instances
from qa_tina_tools.tools.tina import info_keys, wait_tools


@pytest.mark.region_admin
class Test_modify_pin_state(OscTestSuite):

    def setup_method(self, method):
        super(Test_modify_pin_state, self).setup_method(method)

        self.info = None

        try:

            self.info = create_instances(self.a1_r1, state='running')
            self.server_name = self.a1_r1.intel.instance.find(id=self.info[info_keys.INSTANCE_ID_LIST][0]).response.result[0].servers[0].server
            self.cluster_pz = self.a1_r1.intel.hardware.get_details(device=self.server_name).response.result.cluster_pz
            stop_instances(self.a1_r1, self.info[info_keys.INSTANCE_ID_LIST], force=True, wait=True)

        except Exception as error:
            try:
                self.teardown_class()
            except Exception:
                pass
            raise error

    def teardown_method(self, method):
        try:
            if self.info:
                delete_instances(self.a1_r1, self.info)
        finally:
            super(Test_modify_pin_state, self).teardown_method(method)

    def test_T5121_with_server(self):

        inst_id = self.info[info_keys.INSTANCE_ID_LIST][0]
        kvm_selected = None

        # get the kvm of the instance
        all_servers = self.a1_r1.intel.hardware.get_servers()
        # select new kvm from the list of all kvm ready to use that's different to the initial kvm.

        for kvm in all_servers.response.result:
            if self.cluster_pz != self.a1_r1.intel.hardware.get_details(device=kvm.name).response.result.cluster_pz:
                continue
            if kvm.state != 'READY' or kvm.name == self.server_name:
                continue
            kvm_selected = kvm.name
            break

        if not kvm_selected:
            raise OscTestException('Could not find suitable kvm')

        user_data = '-----BEGIN OUTSCALE SECTION-----\npin={}\n-----END OUTSCALE SECTION-----'.format(kvm_selected)
        user_data = base64.b64encode(user_data.encode('utf-8')).decode('utf-8')

        self.a1_r1.fcu.ModifyInstanceAttribute(UserData={'Value': user_data}, InstanceId=inst_id)

        self.a1_r1.fcu.StartInstances(InstanceId=[inst_id])

        wait_tools.wait_instances_state(self.a1_r1, [inst_id], state='running', threshold=5)

        new_kvm_name = self.a1_r1.intel.instance.find(id=inst_id).response.result[0].servers[0].server

        if kvm_selected != new_kvm_name:
            known_error('TINA-5616', 'Modifiying pin in user data is not taken into account at restart')

        assert False, 'Remove the known error code'

    def test_T5122_with_empty_server(self):

        inst_id = self.info[info_keys.INSTANCE_ID_LIST][0]
        initial_kvm = self.server_name

        user_data = '-----BEGIN OUTSCALE SECTION-----\npin=\n-----END OUTSCALE SECTION-----'
        user_data = base64.b64encode(user_data.encode('utf-8')).decode('utf-8')

        self.a1_r1.fcu.ModifyInstanceAttribute(UserData={'Value': user_data}, InstanceId=inst_id)

        self.a1_r1.fcu.StartInstances(InstanceId=[inst_id])

        wait_tools.wait_instances_state(self.a1_r1, [inst_id], state='running', threshold=5)

        new_kvm_name = self.a1_r1.intel.instance.find(id=inst_id).response.result[0].servers[0].server

        assert new_kvm_name

    def test_T5123_with_auto(self):

        inst_id = self.info[info_keys.INSTANCE_ID_LIST][0]
        initial_kvm = self.server_name

        user_data = '-----BEGIN OUTSCALE SECTION-----\npin={}\n-----END OUTSCALE SECTION-----'.format('auto')
        user_data = base64.b64encode(user_data.encode('utf-8')).decode('utf-8')

        self.a1_r1.fcu.ModifyInstanceAttribute(UserData={'Value': user_data}, InstanceId=inst_id)

        self.a1_r1.fcu.StartInstances(InstanceId=[inst_id])

        wait_tools.wait_instances_state(self.a1_r1, [inst_id], state='running', threshold=5)

        new_kvm_name = self.a1_r1.intel.instance.find(id=inst_id).response.result[0].servers[0].server

        assert new_kvm_name
