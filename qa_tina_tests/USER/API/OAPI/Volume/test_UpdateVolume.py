import pytest

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import assert_oapi_error, assert_dry_run, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.specs.check_tools import check_oapi_response
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state


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
        cls.vol = None

    @classmethod
    def teardown_class(cls):
        super(Test_UpdateVolume, cls).teardown_class()

    def setup_method(self, method):
        super(Test_UpdateVolume, self).setup_method(method)
        try:
            self.vol = self.a1_r1.oapi.CreateVolume(VolumeType='standard', Size=2,
                                                    SubregionName=self.azs[0]).response.Volume
            wait_volumes_state(self.a1_r1, [self.vol.VolumeId], state='available')
        except:
            try:
                self.teardown_class()
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.vol:
                self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol.VolumeId)
        finally:
            super(Test_UpdateVolume, self).teardown_method(method)

    def test_T5232_valid_params(self):
        resp = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=5).response
        #wait_volumes_state(self.a1_r1, [self.vol.VolumeId], state='completed')
        check_oapi_response(resp, 'UpdateVolumeResponse')
        if resp.Volume.Size != 5:
            known_error("TINA-5994", "waiting for product decision")
        compare_validate_volumes(self.vol, resp.Volume, Size=5)

    def test_T5233_without_params(self):
        try:
            self.a1_r1.oapi.UpdateVolume()
            assert False, 'Call should not have been successful, missing parameter'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5234_with_dry_run(self):
        resp = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=5, DryRun=True)
        assert_dry_run(resp)

    def test_T5237_without_volume_id(self):
        try:
            self.a1_r1.oapi.UpdateVolume(Size=5)
            assert False, 'Call should not have been successful, missing parameter'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5235_with_unknown_volume_id(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId='vol-12345678', Size=5)
            assert False
        except OscApiException as error:
            assert_error(error, 400, '5064', 'InvalidResource')

    def test_T5240_with_invalid_volume_id_type(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=[self.vol.VolumeId], Size=5)
            assert False
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5239_with_invalid_vol_id(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId='foo', Size=5)
            assert False
        except OscApiException as error:
            assert_error(error, 400, '4104', 'InvalidParameterValue')

    def test_T5236_without_size_volume(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5238_with_invalid_size(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size='foo')
            assert False
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5243_with_invalid_size_type(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=[5])
            assert False
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5244_with_too_big(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=10000000000)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T5245_with_too_small(self):
        ret = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=0)
        if ret.status_code == 200:
            known_error("TINA-5996", "UpdateVolume success with a size 0, waiting for product decision")

    def test_T5241_with_lower_size(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=1)
            assert False
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4078')

    @pytest.mark.tag_sec_confidentiality
    def test_T5242_from_another_account(self):
        try:
            self.a2_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=5)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5064')

    def test_T5322_with_attached_instance(self):
        is_attached = False
        inst_info = None
        try:
            vm_type = self.a1_r1.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE)
            inst_info = create_instances(self.a1_r1, state='running', inst_type=vm_type)
            self.a1_r1.oapi.LinkVolume(VolumeId=self.vol.VolumeId, VmId=inst_info[INSTANCE_ID_LIST][0],
                                       DeviceName='/dev/xvdc')
            wait_volumes_state(self.a1_r1, [self.vol.VolumeId], state='in-use')
            is_attached = True

            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=5)
            assert False, 'Call should not have been successful'

        except OscApiException as error:
            assert_oapi_error(error, 409, 'InvalidState', '6003')

        finally:
            if is_attached:
                self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol.VolumeId)
                wait_volumes_state(self.a1_r1, [self.vol.VolumeId], state='available')
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
