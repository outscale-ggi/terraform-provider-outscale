from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, get_export_value, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.delete_tools import stop_instances, delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state, wait_instances_state


class Test_DeleteVolume(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteVolume, cls).setup_class()
        cls.inst_info = None
        try:
            cls.inst_info = create_instances(cls.a1_r1, state=None)
            cls.inst_info_stopped = create_instances(cls.a1_r1, state='running')
            stop_instances(cls.a1_r1, instance_id_list=cls.inst_info_stopped[INSTANCE_ID_LIST])
            wait_instances_state(cls.a1_r1, cls.inst_info[INSTANCE_ID_LIST], state='running')
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
                delete_instances(cls.a1_r1, cls.inst_info_stopped)
        finally:
            super(Test_DeleteVolume, cls).teardown_class()

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)

    def teardown_method(self, method):
        OscTestSuite.teardown_method(self, method)

    def test_T1170_valid_param_standard_non_attached(self):
        _, volume_ids = create_volumes(self.a1_r1)
        wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, state="available")
        self.a1_r1.fcu.DeleteVolume(VolumeId=volume_ids[0])
        wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, cleanup=True)

    def test_T1171_with_invalid_volume_id(self):
        try:
            self.a1_r1.fcu.DeleteVolume(VolumeId="123456789")
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY', False):
                assert_error(error, 400, 'InvalidParameterValue', None)
                assert not error.message
                known_error('GTW-1367', 'Missing error message')
            assert_error(error, 400, 'InvalidVolumeID.Malformed', "Invalid ID received: 123456789. Expected format: vol-")

    def test_T3993_valid_param_gp2_non_attached(self):
        _, volume_ids = create_volumes(self.a1_r1, volume_type='gp2')
        wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, state="available")
        self.a1_r1.fcu.DeleteVolume(VolumeId=volume_ids[0])
        wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, cleanup=True)

    def test_T3994_valid_param_io1_non_attached(self):
        _, volume_ids = create_volumes(self.a1_r1, volume_type='io1', iops=150)
        wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, state="available")
        self.a1_r1.fcu.DeleteVolume(VolumeId=volume_ids[0])
        wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, cleanup=True)

    def test_T3995_valid_param_standard_attached(self):
        _, volume_ids = create_volumes(self.a1_r1)
        wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, state="available")
        rslt_attach = self.a1_r1.fcu.AttachVolume(VolumeId=volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdb")
        wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, state="in-use")
        try:
            self.a1_r1.fcu.DeleteVolume(VolumeId=volume_ids[0])
            wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, cleanup=True)
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY', False):
                assert_error(error, 409, 'InvalidState', None)
                assert not error.message
                known_error('GTW-1367', 'Incorrect error code and status or missing error message')
            assert_error(error, 400, 'VolumeInUse', "Volume '{}' is currently attached to instance: {}".format(volume_ids[0],
                                                                                                               self.inst_info[INSTANCE_ID_LIST][0]))
        finally:
            if rslt_attach:
                self.a1_r1.fcu.DetachVolume(VolumeId=volume_ids[0])
                wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, state="available")
            self.a1_r1.fcu.DeleteVolume(VolumeId=volume_ids[0])
            wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, cleanup=True)

    def test_T3996_valid_param_gp2_attached(self):
        _, volume_ids = create_volumes(self.a1_r1, volume_type='gp2')
        wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, state="available")
        rslt_attach = self.a1_r1.fcu.AttachVolume(VolumeId=volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdc")
        wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, state="in-use")
        try:
            self.a1_r1.fcu.DeleteVolume(VolumeId=volume_ids[0])
            wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, cleanup=True)
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY', False):
                assert_error(error, 409, 'InvalidState', None)
                assert not error.message
                known_error('GTW-1367', 'Incorrect error code and status or missing error message')
            assert_error(error, 400, 'VolumeInUse', "Volume '{}' is currently attached to instance: {}".format(volume_ids[0],
                                                                                                               self.inst_info[INSTANCE_ID_LIST][0]))
        finally:
            if rslt_attach:
                self.a1_r1.fcu.DetachVolume(VolumeId=volume_ids[0])
                wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, state="available")
            self.a1_r1.fcu.DeleteVolume(VolumeId=volume_ids[0])
            wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, cleanup=True)

    def test_T3997_valid_param_io1_attached(self):
        _, volume_ids = create_volumes(self.a1_r1, volume_type='io1', iops=150)
        wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, state="available")
        rslt_attach = self.a1_r1.fcu.AttachVolume(VolumeId=volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdd")
        wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, state="in-use")
        try:
            self.a1_r1.fcu.DeleteVolume(VolumeId=volume_ids[0])
            wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, cleanup=True)
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY', False):
                assert_error(error, 409, 'InvalidState', None)
                assert not error.message
                known_error('GTW-1367', 'Incorrect error code and status or missing error message')
            assert_error(error, 400, 'VolumeInUse', "Volume '{}' is currently attached to instance: {}".format(volume_ids[0],
                                                                                                               self.inst_info[INSTANCE_ID_LIST][0]))
        finally:
            if rslt_attach:
                self.a1_r1.fcu.DetachVolume(VolumeId=volume_ids[0])
                wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, state="available")
            self.a1_r1.fcu.DeleteVolume(VolumeId=volume_ids[0])
            wait_volumes_state(self.a1_r1, volume_id_list=volume_ids, cleanup=True)
