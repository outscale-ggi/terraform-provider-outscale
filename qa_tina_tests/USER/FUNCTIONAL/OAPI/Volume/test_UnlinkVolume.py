

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools import misc
from qa_tina_tools.tina import oapi, wait, info_keys

DEVICE_NAME = '/dev/xvdc'


class Test_UnlinkVolume(OscTestSuite):

    def test_T5581_inst_running_vol_creating(self):
        vm_info = None
        vol_id = None
        try:
            vm_info = oapi.create_Vms(self.a1_r1, state='running')
            vol_id = self.a1_r1.oapi.CreateVolume(VolumeType='standard', Size=2,
                                                  SubregionName=self.azs[0]).response.Volume.VolumeId
            self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
            assert False, 'Call should not be successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 409, 'InvalidState', '6003')
        finally:
            if vol_id:
                wait.wait_Volumes_state(self.a1_r1, [vol_id], state='available')
                self.a1_r1.oapi.DeleteVolume(VolumeId=vol_id)
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)

    def test_T5582_inst_running_vol_available(self):
        vm_info = None
        vol_id = None
        try:
            vm_info = oapi.create_Vms(self.a1_r1, state='running')
            vol_id = self.a1_r1.oapi.CreateVolume(VolumeType='standard', Size=2,
                                                  SubregionName=self.azs[0]).response.Volume.VolumeId
            wait.wait_Volumes_state(self.a1_r1, [vol_id], 'available')
            self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
            assert False, 'Call should not be successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 409, 'InvalidState', '6003')
        finally:
            if vol_id:
                wait.wait_Volumes_state(self.a1_r1, [vol_id], state='available')
                self.a1_r1.oapi.DeleteVolume(VolumeId=vol_id)
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)

    def test_T5583_inst_running_vol_attaching(self):
        vm_info = None
        vol_id = None
        try:
            vm_info = oapi.create_Vms(self.a1_r1, state='running')
            vol_id = self.a1_r1.oapi.CreateVolume(VolumeType='standard', Size=2,
                                                  SubregionName=self.azs[0]).response.Volume.VolumeId
            wait.wait_Volumes_state(self.a1_r1, [vol_id], 'available')
            self.a1_r1.oapi.LinkVolume(VolumeId=vol_id,
                                                  VmId=vm_info[info_keys.VM_IDS][0],
                                                  DeviceName=DEVICE_NAME)
            self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
        finally:
            try:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
            except:
                self.logger('Could not unlink volume')
            if vol_id:
                wait.wait_Volumes_state(self.a1_r1, [vol_id], state='available')
                self.a1_r1.oapi.DeleteVolume(VolumeId=vol_id)
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)

    def test_T5584_inst_running_vol_attached(self):
        vm_info = None
        vol_id = None
        try:
            vm_info = oapi.create_Vms(self.a1_r1, state='running')
            vol_id = self.a1_r1.oapi.CreateVolume(VolumeType='standard', Size=2,
                                                  SubregionName=self.azs[0]).response.Volume.VolumeId
            wait.wait_Volumes_state(self.a1_r1, [vol_id], 'available')
            self.a1_r1.oapi.LinkVolume(VolumeId=vol_id,
                                                  VmId=vm_info[info_keys.VM_IDS][0],
                                                  DeviceName=DEVICE_NAME)
            wait.wait_Volumes_state(self.a1_r1, [vol_id], 'in-use')
            self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
        finally:
            try:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
            except:
                self.logger('Could not unlink volume')
            if vol_id:
                wait.wait_Volumes_state(self.a1_r1, [vol_id], state='available')
                self.a1_r1.oapi.DeleteVolume(VolumeId=vol_id)
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)

    def test_T5585_inst_running_vol_detaching(self):
        vm_info = None
        vol_id = None
        try:
            vm_info = oapi.create_Vms(self.a1_r1, state='running')
            vol_id = self.a1_r1.oapi.CreateVolume(VolumeType='standard', Size=2,
                                                  SubregionName=self.azs[0]).response.Volume.VolumeId
            wait.wait_Volumes_state(self.a1_r1, [vol_id], 'available')
            self.a1_r1.oapi.LinkVolume(VolumeId=vol_id,
                                                  VmId=vm_info[info_keys.VM_IDS][0],
                                                  DeviceName=DEVICE_NAME)
            wait.wait_Volumes_state(self.a1_r1, [vol_id], 'in-use')
            self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
            self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
        finally:
            try:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
            except:
                self.logger('Could not unlink volume')
            if vol_id:
                wait.wait_Volumes_state(self.a1_r1, [vol_id], state='available')
                self.a1_r1.oapi.DeleteVolume(VolumeId=vol_id)
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)

    def test_T5586_inst_starting_unlink_boot(self):
        vm_info = None
        vol_id = None
        try:
            vm_info = oapi.create_Vms(self.a1_r1, state=None)
            vol_id = vm_info[info_keys.VMS][0]['BlockDeviceMappings'][0]['Bsu']['VolumeId']
            self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
            assert False, 'Call should not be successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'OperationNotSupported', '8003')
        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)

    def test_T5587_inst_running_unlink_boot(self):
        vm_info = None
        vol_id = None
        try:
            vm_info = oapi.create_Vms(self.a1_r1, state='running')
            vol_id = vm_info[info_keys.VMS][0]['BlockDeviceMappings'][0]['Bsu']['VolumeId']
            self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
            assert False, 'Call should not be successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'OperationNotSupported', '8003')
        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)

    def test_T5588_inst_stopping_unlink_boot(self):
        vm_info = None
        vol_id = None
        try:
            vm_info = oapi.create_Vms(self.a1_r1, state='running')
            oapi.stop_Vms(self.a1_r1, vm_info[info_keys.VM_IDS], wait_state=False)
            vol_id = vm_info[info_keys.VMS][0]['BlockDeviceMappings'][0]['Bsu']['VolumeId']
            self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
            assert False, 'Call should not be successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'OperationNotSupported', '8003')
        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)

    def test_T5589_inst_stopped_unlink_boot(self):
        vm_info = None
        vol_id = None
        try:
            vm_info = oapi.create_Vms(self.a1_r1, state='stopped')
            oapi.stop_Vms(self.a1_r1, vm_info[info_keys.VM_IDS], wait_state=True)
            vol_id = vm_info[info_keys.VMS][0]['BlockDeviceMappings'][0]['Bsu']['VolumeId']
            self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)

    def test_T5590_inst_terminating_unlink_boot(self):
        vm_info = None
        vol_id = None
        try:
            vm_info = oapi.create_Vms(self.a1_r1, state='running')
            oapi.terminate_Vms(self.a1_r1, vm_info[info_keys.VM_IDS], wait_state=False)
            vol_id = vm_info[info_keys.VMS][0]['BlockDeviceMappings'][0]['Bsu']['VolumeId']
            self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
            assert False, 'Call should not be successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'OperationNotSupported', '8003')

    def test_T5591_inst_terminated_unlink_boot(self):
        vm_info = None
        vol_id = None
        try:
            vm_info = oapi.create_Vms(self.a1_r1, state='running')
            oapi.terminate_Vms(self.a1_r1, vm_info[info_keys.VM_IDS], wait_state=True)
            vol_id = vm_info[info_keys.VMS][0]['BlockDeviceMappings'][0]['Bsu']['VolumeId']
            self.a1_r1.oapi.UnlinkVolume(VolumeId=vol_id)
            assert False, 'Call should not be successful'
        except OscApiException as error:
            try:
                misc.assert_oapi_error(error, 400, 'InvalidResource', '5064')
            except AssertionError:
                misc.assert_oapi_error(error, 409, 'InvalidState', '6003')
