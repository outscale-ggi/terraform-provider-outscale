
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state


class Test_LinkVolume(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        cls.vol_id = None
        cls.ret_link = None
        super(Test_LinkVolume, cls).setup_class()
        try:
            cls.inst_info = create_instances(cls.a1_r1)
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_LinkVolume, cls).teardown_class()

    def setup_method(self, method):
        self.vol_id = None
        self.ret_link = None
        OscTestSuite.setup_method(self, method)
        try:
            self.vol_id = self.a1_r1.oapi.CreateVolume(SubregionName=self.azs[0], Size=10).response.Volume.VolumeId
            wait_volumes_state(self.a1_r1, [self.vol_id], state='available')
        except:
            try:
                self.teardown_method(method)
            finally:
                raise

    def teardown_method(self, method):
        try:
            if self.ret_link:
                try:
                    self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_id)
                    wait_volumes_state(self.a1_r1, [self.vol_id], state='available')
                except:
                    print('Could not detach volume')
            if self.vol_id:
                try:
                    self.a1_r1.oapi.DeleteVolume(VolumeId=self.vol_id)
                except:
                    print('Could not delete volume')
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T2254_valid_params(self):
        self.ret_link = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id, VmId=self.inst_info[INSTANCE_ID_LIST][0], DeviceName='/dev/xvdc')
        wait_volumes_state(self.a1_r1, [self.vol_id], state='in-use')

    def test_T2255_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.LinkVolume(VolumeId=self.vol_id, VmId=self.inst_info[INSTANCE_ID_LIST][0], DeviceName='/dev/xvdc', DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3545_other_account(self):
        try:
            self.ret_link = self.a2_r1.oapi.LinkVolume(VolumeId=self.vol_id, VmId=self.inst_info[INSTANCE_ID_LIST][0], DeviceName='/dev/xvdc')
            wait_volumes_state(self.a1_r1, [self.vol_id], state='in-use')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')
