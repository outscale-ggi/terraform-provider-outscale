from qa_test_tools.test_base import OscTestSuite, get_export_value, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error


class Test_DetachVolume(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        super(Test_DetachVolume, cls).setup_class()
        try:
            cls.inst_info = create_instances(cls.a1_r1, nb=2)
            _, cls.standard_volume_ids = create_volumes(cls.a1_r1, count=2)
            _, cls.gp2_volume_ids = create_volumes(cls.a1_r1, volume_type='gp2')
            _, cls.io1_volume_ids = create_volumes(cls.a1_r1, volume_type='io1', iops=150)
            wait_volumes_state(cls.a1_r1, cls.standard_volume_ids, 'available')
            wait_volumes_state(cls.a1_r1, cls.io1_volume_ids, 'available')
            wait_volumes_state(cls.a1_r1, cls.standard_volume_ids, 'available')
            cls.rslt_attach_standard = cls.a1_r1.fcu.AttachVolume(VolumeId=cls.standard_volume_ids[0], InstanceId=cls.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdb")
            cls.a1_r1.fcu.AttachVolume(VolumeId=cls.standard_volume_ids[1], InstanceId=cls.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvde")
            cls.rslt_attach_gp2 = cls.a1_r1.fcu.AttachVolume(VolumeId=cls.gp2_volume_ids[0], InstanceId=cls.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdc")
            cls.rslt_attach_io1 = cls.a1_r1.fcu.AttachVolume(VolumeId=cls.io1_volume_ids[0], InstanceId=cls.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdd")
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
                delete_instances(cls.a1_r1, cls.inst_info)
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.standard_volume_ids[0])
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.standard_volume_ids[1])
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.gp2_volume_ids[0])
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.io1_volume_ids[0])
        finally:
            super(Test_DetachVolume, cls).teardown_class()

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        self.rslt_detach_standard = None
        self.rslt_detach_gp2 = None
        self.rslt_detach_io1 = None

    def teardown_method(self, method):
        try:
            if self.rslt_detach_standard:
                self.rslt_attach_standard = self.a1_r1.fcu.AttachVolume(VolumeId=self.standard_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdb")
                wait_volumes_state(self.a1_r1, volume_id_list=self.standard_volume_ids, state="in-use")
            if self.rslt_detach_gp2:
                self.rslt_attach_gp2 = self.a1_r1.fcu.AttachVolume(VolumeId=self.gp2_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdc")
                wait_volumes_state(self.a1_r1, volume_id_list=self.gp2_volume_ids, state="in-use")
            if self.rslt_detach_io1:
                self.rslt_attach_io1 = self.a1_r1.fcu.AttachVolume(VolumeId=self.io1_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdd")
                wait_volumes_state(self.a1_r1, volume_id_list=self.io1_volume_ids, state="in-use")
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T1252_valid_param_standard(self):
        self.rslt_detach_standard = self.a1_r1.fcu.DetachVolume(VolumeId=self.standard_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0])
        wait_volumes_state(self.a1_r1, volume_id_list=[self.standard_volume_ids[0]], state="available")

    def test_T3958_valid_param_gp2(self):
        self.rslt_detach_gp2 = self.a1_r1.fcu.DetachVolume(VolumeId=self.gp2_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0])
        wait_volumes_state(self.a1_r1, volume_id_list=[self.gp2_volume_ids[0]], state="available")

    def test_T3959_valid_param_io1(self):
        self.rslt_detach_io1 = self.a1_r1.fcu.DetachVolume(VolumeId=self.io1_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0])
        wait_volumes_state(self.a1_r1, volume_id_list=[self.io1_volume_ids[0]], state="available")

    def test_T1255_option_force_standard(self):
        self.rslt_detach_standard = self.a1_r1.fcu.DetachVolume(VolumeId=self.standard_volume_ids[0],
                                                              InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Force=True)
        wait_volumes_state(self.a1_r1, volume_id_list=[self.standard_volume_ids[0]], state="available")

    def test_T3960_option_force_gp2(self):
        self.rslt_detach_gp2 = self.a1_r1.fcu.DetachVolume(VolumeId=self.gp2_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Force=True)
        wait_volumes_state(self.a1_r1, volume_id_list=[self.gp2_volume_ids[0]], state="available")

    def test_T3961_option_force_io1(self):
        self.rslt_detach_io1 = self.a1_r1.fcu.DetachVolume(VolumeId=self.io1_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Force=True)
        wait_volumes_state(self.a1_r1, volume_id_list=[self.io1_volume_ids[0]], state="available")

    def test_T1254_non_existing_volume_id(self):
        try:
            self.rslt_detach_standard = self.a1_r1.fcu.DetachVolume(VolumeId="vol-aaaaaaaa", InstanceId=self.inst_info[INSTANCE_ID_LIST][0])
            assert False, "Call should not be successful"
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY', False):
                assert_error(error, 400, 'InvalidVolume.NotFound', None)
                assert not error.message
                known_error('GTW-1370', 'Missing error message')
            assert_error(error, 400, 'InvalidVolume.NotFound', "The volume 'vol-aaaaaaaa' does not exist.")

    def test_T1253_non_attached_volume_id(self):
        self.rslt_detach_standard = self.a1_r1.fcu.DetachVolume(VolumeId=self.standard_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0])
        wait_volumes_state(self.a1_r1, volume_id_list=[self.standard_volume_ids[0]], state="available")
        try:
            self.rslt_detach_standard = self.a1_r1.fcu.DetachVolume(VolumeId=self.standard_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0])
            assert False, "Call should not be successful"
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY', False):
                assert_error(error, 409, 'InvalidState', None)
                assert not error.message
                known_error('GTW-1370', 'Incorrect error code and status, missing error message')
            assert_error(error, 400, "InvalidParameterValue", "Given Instance {} and Volume {} are not attached".format(self.inst_info[INSTANCE_ID_LIST][0], self.standard_volume_ids[0]))

    def test_T5028_from_an_other_instance(self):
        try:
            self.rslt_detach_standard = self.a1_r1.fcu.DetachVolume(VolumeId=self.standard_volume_ids[1], InstanceId=self.inst_info[INSTANCE_ID_LIST][1])
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterValue", "Given Instance {} and Volume {} are not attached".format(self.inst_info[INSTANCE_ID_LIST][1], self.standard_volume_ids[1]))
