# -*- coding:utf-8 -*-
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state


class Test_UnlinkVolume(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UnlinkVolume, cls).setup_class()
        cls.inst_info = None
        try:
            cls.inst_info = create_instances(cls.a1_r1)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info:
                try:
                    delete_instances(cls.a1_r1, cls.inst_info)
                except:
                    pass
        finally:
            super(Test_UnlinkVolume, cls).teardown_class()

    def setup_method(self, method):
        self.vol_id = None
        self.ret_link = None
        OscTestSuite.setup_method(self, method)
        try:
            self.vol_id = self.a1_r1.oapi.CreateVolume(SubregionName=self.azs[0], Size=10).response.Volume.VolumeId
            wait_volumes_state(self.a1_r1, [self.vol_id], state='available')
            self.ret_link = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id, VmId=self.inst_info[INSTANCE_ID_LIST][0], DeviceName='/dev/xvdc')
            wait_volumes_state(self.a1_r1, [self.vol_id], state='in-use')
        except:
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.ret_link:
                try:
                    self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_id)
                    wait_volumes_state(self.a1_r1, [self.vol_id], state='available')
                except:
                    pass
            if self.vol_id:
                try:
                    self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol_id)
                except:
                    pass
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T2256_valid_params(self):
        self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id)
        wait_volumes_state(self.a1_r1, [self.vol_id], state='available')
        self.ret_link = None

    def test_T2257_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id, DryRun=True)
        assert_dry_run(ret)

    def test_T4140_with_device_name(self):
        try:
            self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    @pytest.mark.tag_sec_confidentiality
    def test_T3546_other_account(self):
        try:
            self.a2_r1.oapi.UnlinkVolume(VolumeId=self.vol_id)
            wait_volumes_state(self.a1_r1, [self.vol_id], state='available')
            self.ret_link = None
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5064')

    @pytest.mark.region_admin
    def test_T5129_with_force_unlink_false(self):
        self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id, ForceUnlink=False)
        wait_volumes_state(self.a1_r1, [self.vol_id], state='available')

    @pytest.mark.region_admin
    def test_T5130_with_force_unlink_true(self):
        self.a1_r1.oapi.UnlinkVolume(VolumeId=self.vol_id, ForceUnlink=True)
        wait_volumes_state(self.a1_r1, [self.vol_id], state='available')
