
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_dry_run
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state


class Test_DeleteVolume(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteVolume, cls).setup_class()
        cls.vol_id = None

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteVolume, cls).teardown_class()

    def teardown_method(self, method):
        try:
            if self.vol_id:
                self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol_id)
                self.vol_id = None
        finally:
            super(Test_DeleteVolume, self).teardown_method(method)

    def create_volume(self):
        vol_id = None
        try:
            vol_id = self.a1_r1.oapi.CreateVolume(SubregionName=self.azs[0], Size=10).response.Volume.VolumeId
            wait_volumes_state(self.a1_r1, [vol_id], state='available')
        except:
            print('create_volume failed')
        return vol_id

    def test_T2252_valid_params(self):
        self.vol_id = self.create_volume()
        self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol_id)
        self.vol_id = None

    def test_T2253_valid_params_dry_run(self):
        self.vol_id = self.create_volume()
        ret = self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol_id, DryRun=True)
        assert_dry_run(ret)

    def test_T2964_missing_param(self):
        try:
            self.a1_r1.oapi.DeleteVolume()
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2965_invalid_volume_id(self):
        try:
            self.a1_r1.oapi.DeleteVolume(VolumeId='tata')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2966_malformed_volume_id(self):
        try:
            self.a1_r1.oapi.DeleteVolume(VolumeId='vol-123456')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')

    def test_T2967_unknown_volume_id(self):
        try:
            self.a1_r1.oapi.DeleteVolume(VolumeId='vol-12345678')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5064')

    @pytest.mark.tag_sec_confidentiality
    def test_T3520_with_other_user(self):
        try:
            self.vol_id = self.create_volume()
            self.a2_r1.oapi.DeleteVolume(VolumeId=self.vol_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5064')
