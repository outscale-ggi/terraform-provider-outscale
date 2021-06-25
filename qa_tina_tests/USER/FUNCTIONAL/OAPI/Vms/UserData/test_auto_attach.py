
import base64
import pytest

from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tina import oapi, info_keys, wait

class Test_auto_attach(OscTestSuite):

    def test_T5763_auto_attach(self):
        public_ip = None
        vm_info1 = None
        vm_info2 = None
        try:
            public_ip = self.a1_r1.oapi.CreatePublicIp().response.PublicIp.PublicIp
            userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.eip.auto-attach={}
            -----END OUTSCALE SECTION-----""".format(public_ip)
            vm_info1 = oapi.create_Vms(self.a1_r1, user_data=base64.b64encode(userdata.encode('utf-8')).decode('utf-8'))
            oapi.stop_Vms(self.a1_r1, vm_info1[info_keys.VM_IDS])
            vm_info2 = oapi.create_Vms(self.a1_r1)
            self.a1_r1.oapi.LinkPublicIp(VmId=vm_info2[info_keys.VM_IDS][0], PublicIp=public_ip)

            oapi.start_Vms(self.a1_r1, vm_info1[info_keys.VM_IDS], state=None, wait=False)
            try:
                wait.wait_Vms_state(self.a1_r1, vm_info1[info_keys.VM_IDS], 'running')
                known_error('TINA-6577', 'Vm should not have started as auto attached eip is already attached.')
            except AssertionError:
                pytest.fail('Remove known error code')

        finally:
            if vm_info1:
                oapi.delete_Vms(self.a1_r1, vm_info1)
            if vm_info2:
                oapi.delete_Vms(self.a1_r1, vm_info2)
            if public_ip:
                self.a1_r1.oapi.DeletePublicIp(PublicIp=public_ip)
