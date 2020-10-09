import pytest

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite
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

    @classmethod
    def teardown_class(cls):
        super(Test_UpdateVolume, cls).teardown_class()

    def setup_method(self, method):
        super(Test_UpdateVolume, self).setup_method(method)
        self.vol = None
        try:
            self.vol = self.a1_r1.oapi.CreateVolume(VolumeType='standard', Size=2,
                                                    SubregionName=self.azs[0]).response.Volume
            wait_volumes_state(self.a1_r1, self.vol.VolumeId, state='available')
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

    def test_T5235_with_dry_run_false(self):
        resp = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=5, DryRun=False)
        assert_dry_run(resp)

    def test_T5236_without_size_volume(self):
        resp = self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId).response.Volume
        compare_validate_volumes(self.vol, resp.Volume)

    def test_T5237_without_volume_id(self):
        try:
            self.a1_r1.oapi.UpdateVolume(Size=5)
            assert False, 'Call should not have been successful, missing parameter'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5238_with_invalid_size(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size='foo')
            assert False
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T5239_with_invalid_vol_id(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId='foo', Size=5)
            assert False
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T5240_with_size_max(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=20000)
            assert False
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T5241_with_size_min(self):
        try:
            self.a1_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=1)
            assert False
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    @pytest.mark.tag_sec_confidentiality
    def test_T5242_from_another_account(self):
        try:
            self.a2_r1.oapi.UpdateVolume(VolumeId=self.vol.VolumeId, Size=5)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5064')
