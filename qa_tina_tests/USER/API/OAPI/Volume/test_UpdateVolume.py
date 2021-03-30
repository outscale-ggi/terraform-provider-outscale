import time

import pytest

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import assert_oapi_error, assert_dry_run, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tina.wait import wait_Vms_state, wait_Volumes_state
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state

NEW_SIZE = 8


def compare_validate_volumes(before_volume, after_volume, **kwargs):
    for kwarg in kwargs:
        assert getattr(after_volume, kwarg) == kwargs[kwarg]
    for attr in before_volume.__dict__:
        if not attr.startswith('_') and attr not in kwargs:
            assert getattr(before_volume, attr) == getattr(after_volume, attr)


class Test_UpdateVolume(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateVolume, cls).setup_class()
        cls.vol_ids = dict()
        cls.vm_info = None
        try:
            image_id = cls.a1_r1.config.region.get_info(constants.CENTOS7)
            cls.vm_info = cls.a1_r1.oapi.CreateVms(ImageId=image_id).response.Vms[0]
            wait_Vms_state(cls.a1_r1, [cls.vm_info.VmId], state='running')

        except Exception as error:
            try:
                cls.teardown_class()
            except Exception as err:
                raise err
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vm_info:
                cls.a1_r1.oapi.DeleteVms(VmIds=[cls.vm_info.VmId])
                wait_Vms_state(cls.a1_r1, [cls.vm_info.VmId], state='terminated')
        finally:
            super(Test_UpdateVolume, cls).teardown_class()

    def setup_method(self, method):
        super(Test_UpdateVolume, self).setup_method(method)
        self.vol_ids = dict()
        try:
            az_name = self.a1_r1.config.region.az_name
            self.vol_ids['standard'] = self.a1_r1.oapi.CreateVolume(VolumeType='standard', Size=4,
                                                                    SubregionName=az_name).response.Volume.VolumeId
            self.vol_ids['io1'] = self.a1_r1.oapi.CreateVolume(VolumeType='io1', Size=4, Iops=150,
                                                               SubregionName=az_name).response.Volume.VolumeId
            self.vol_ids['gp2'] = self.a1_r1.oapi.CreateVolume(VolumeType='gp2', Size=4,
                                                               SubregionName=az_name).response.Volume.VolumeId
            wait_volumes_state(self.a1_r1, list(self.vol_ids.values()), state='available')

        except Exception as error:
            try:
                self.teardown_method(method)
            except Exception as err:
                raise err
            finally:
                raise error

    def teardown_method(self, method):
        try:
            for vol_id in self.vol_ids.values():
                self.a1_r1.oapi.DeleteVolume(VolumeId=vol_id)
        finally:
            super(Test_UpdateVolume, self).teardown_method(method)

    def test_T5232_valid_params(self):
        ret = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'], Size=NEW_SIZE)
        ret.check_response()
        if ret.response.Volume.Size != NEW_SIZE:
            known_error('PRODUCT-282', 'Waiting product decision on this.')
        assert False, 'Remove known error'
        for _ in range(10):
            resp = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeIds': [ret.response.Volume.VolumeId]}).response
            if resp.Volumes[0].Size == NEW_SIZE:
                break
            time.sleep(2)
        assert resp.Volumes[0].Size == NEW_SIZE
        compare_validate_volumes(self.vol, resp.Volumes[0], Size=NEW_SIZE, State='available')

    def test_T5233_without_params(self):
        try:
            self.a1_r1.oapi.UpdateVolume()
            assert False, 'Call should not have been successful, missing parameter'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5234_with_dry_run(self):
        resp = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'], Size=NEW_SIZE, DryRun=True)
        assert_dry_run(resp)

    def test_T5237_without_volume_id(self):
        try:
            self.a1_r1.oapi.UpdateVolume(Size=NEW_SIZE)
            assert False, 'Call should not have been successful, missing parameter'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5235_with_unknown_volume_id(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId='vol-12345678', Size=NEW_SIZE)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, '5064', 'InvalidResource')

    def test_T5240_with_invalid_volume_id_type(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=[self.vol_ids['standard']], Size=NEW_SIZE)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5239_with_invalid_vol_id(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId='foo', Size=NEW_SIZE)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, '4104', 'InvalidParameterValue')

    def test_T5236_without_size_volume(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'])
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7006')

    def test_T5238_with_invalid_size(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'], Size='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5243_with_invalid_size_type(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'], Size=[NEW_SIZE])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5244_with_too_big(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'], Size=10000000000)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4078')

    def test_T5245_with_too_small(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'], Size=0)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4135')

    def test_T5241_with_lower_size(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'], Size=1)
            known_error('TINA-6368', 'Regression UpdateVolume')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert False, 'Remove known error'
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4078')

    @pytest.mark.tag_sec_confidentiality
    def test_T5242_from_another_account(self):
        try:
            self.a2_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'], Size=NEW_SIZE)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5064')

    def test_T5322_with_attached_instance(self):
        linked = None
        try:
            linked = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_ids['standard'], VmId=self.vm_info.VmId,
                                                DeviceName='/dev/xvdc')
            wait_Volumes_state(self.a1_r1, [self.vol_ids['standard']], 'in-use')
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'], Size=NEW_SIZE)
            assert False, 'Call should not have been successful'

        except OscApiException as error:
            assert_oapi_error(error, 409, 'InvalidState', '6003')

        finally:
            if linked:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_ids['standard'])
                wait_Volumes_state(self.a1_r1, [self.vol_ids['standard']], 'available')

    def test_T5592_with_vol_type_std_io1(self):
        ret = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'], VolumeType='io1', Iops=200).response
        assert ret.Volume.VolumeType == 'io1'
        assert ret.Volume.Iops == 200
        assert ret.Volume.VolumeId == self.vol_ids['standard']
        ret = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['io1'], VolumeType='standard').response
        assert ret.Volume.VolumeType == 'standard'
        assert ret.Volume.Iops
        assert ret.Volume.VolumeId == self.vol_ids['io1']

    def test_T5593_with_vol_type_io1_gp2(self):
        ret = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['io1'], VolumeType='gp2').response
        assert ret.Volume.VolumeType == 'gp2'
        assert ret.Volume.Iops
        assert ret.Volume.VolumeId == self.vol_ids['io1']
        ret = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['gp2'], VolumeType='io1', Iops=200).response
        assert ret.Volume.VolumeType == 'io1'
        assert ret.Volume.Iops
        assert ret.Volume.VolumeId == self.vol_ids['gp2']

    def test_T5594_with_vol_type_gp2_std(self):
        ret = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['gp2'], VolumeType='standard').response
        assert ret.Volume.VolumeType == 'standard'
        assert ret.Volume.VolumeId == self.vol_ids['gp2']
        ret = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'], VolumeType='gp2').response
        assert ret.Volume.VolumeType == 'gp2'
        assert ret.Volume.VolumeId == self.vol_ids['standard']

    def test_T5595_with_invalid_type_vol_type(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'], VolumeType=['io1'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, '4110', 'InvalidParameterValue')

    def test_T5596_with_invalid_vol_type(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'], VolumeType='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, '4129', 'InvalidParameterValue')

    def test_T5597_with_iops(self):
        ret = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['io1'], Iops=200).response
        assert ret.Volume.VolumeType == 'io1'
        assert ret.Volume.Iops == 200

    def test_T5598_with_invalid_iops(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['io1'], Iops='foo')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, '4110', 'InvalidParameterValue')

    def test_T5599_with_invalid_iops_type(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['io1'], Iops=[200])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, '4110', 'InvalidParameterValue')

    def test_T5600_with_iops_too_small(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['io1'], Iops=0)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, '4047', 'InvalidParameterValue')

    def test_T5601_with_iops_too_big(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['io1'], Iops=13001)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, '4029', 'InvalidParameterValue')

    def test_T5602_with_lower_iops(self):
        ret = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['io1'], Iops=100).response
        assert ret.Volume.VolumeType == 'io1'
        assert ret.Volume.Iops == 100

    def test_T5603_with_type_hot_vol_running_vm(self):
        linked = None
        try:
            linked = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_ids['standard'], VmId=self.vm_info.VmId, DeviceName='/dev/xvdc')
            wait_Volumes_state(self.a1_r1, [self.vol_ids['standard']], 'in-use')

            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['standard'], VolumeType='gp2')
            assert False, 'Call should not have been successful'

        except OscApiException as error:
            assert_oapi_error(error, 409, 'InvalidState', '6003')

        finally:
            if linked:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_ids['standard'])
                wait_Volumes_state(self.a1_r1, [self.vol_ids['standard']], 'available')

    def test_T5604_with_iops_hot_vol_running_vm(self):
        linked = None
        try:
            linked = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_ids['io1'], VmId=self.vm_info.VmId, DeviceName='/dev/xvdc')
            wait_Volumes_state(self.a1_r1, [self.vol_ids['io1']], 'in-use')
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol_ids['io1'], Iops=200)
            known_error('TINA-6366', 'UpdateVolume')
            assert False, 'Call should not have been successful'

        except OscApiException as error:
            assert False, 'Remove known error'
            assert_oapi_error(error, 409, 'InvalidState', '6003')

        finally:
            if linked:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_ids['io1'])
                wait_Volumes_state(self.a1_r1, [self.vol_ids['io1']], 'available')
