
import base64


from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import oapi, info_keys


class Test_private_ip_only(OscTinaTest):

    def test_T5729_none_to_private_only_true(self):
        vm_info = None
        try:
            data_true = base64.b64encode(
                '-----BEGIN OUTSCALE SECTION-----\nprivate_only=true\n-----END OUTSCALE SECTION-----'.encode()).decode().strip()
            vm_info = oapi.create_Vms(self.a1_r1)
            vm_id = vm_info[info_keys.VM_IDS][0]
            ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [vm_id]})
            assert hasattr(ret.response.Vms[0], 'PublicIp')
            oapi.stop_Vms(self.a1_r1, [vm_id])
            ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [vm_id]})
            assert not hasattr(ret.response.Vms[0], 'PublicIp')
            self.a1_r1.oapi.UpdateVm(UserData=data_true, VmId=vm_id)
            ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [vm_id]})
            assert not hasattr(ret.response.Vms[0], 'PublicIp')
            oapi.start_Vms(self.a1_r1, [vm_id], state='running')
            ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [vm_id]})
            assert not hasattr(ret.response.Vms[0], 'PublicIp')
        except OscApiException as error:
            raise error
        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
