from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state
from qa_common_tools.misc import assert_error, id_generator
from osc_common.exceptions.osc_exceptions import OscApiException
import string


class Test_AttachVolume(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        super(Test_AttachVolume, cls).setup_class()
        try:
            cls.inst_info = create_instances(cls.a1_r1)
            cls.inst_info_stopped = create_instances(cls.a1_r1)
            stop_instances(cls.a1_r1, instance_id_list=cls.inst_info_stopped[INSTANCE_ID_LIST])
            _, cls.standard_volume_ids = create_volumes(cls.a1_r1)
            _, cls.gp2_volume_ids = create_volumes(cls.a1_r1, volume_type='gp2')
            _, cls.io1_volume_ids = create_volumes(cls.a1_r1, volume_type='io1', iops=150)
            wait_volumes_state(cls.a1_r1, cls.standard_volume_ids, 'available')
            wait_volumes_state(cls.a1_r1, cls.io1_volume_ids, 'available')
            wait_volumes_state(cls.a1_r1, cls.standard_volume_ids, 'available')
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
                delete_instances(cls.a1_r1, cls.inst_info_stopped)
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.standard_volume_ids[0])
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.gp2_volume_ids[0])
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.io1_volume_ids[0])
        finally:
            super(Test_AttachVolume, cls).teardown_class()

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        self.rslt_attach_standard = None
        self.rslt_attach_gp2 = None
        self.rslt_attach_io1 = None

    def teardown_method(self, method):
        try:
            if self.rslt_attach_standard:
                self.a1_r1.fcu.DetachVolume(VolumeId=self.standard_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0])
                wait_volumes_state(self.a1_r1, volume_id_list=self.standard_volume_ids, state="available")
            if self.rslt_attach_gp2:
                self.a1_r1.fcu.DetachVolume(VolumeId=self.gp2_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0])
                wait_volumes_state(self.a1_r1, volume_id_list=self.gp2_volume_ids, state="available")
            if self.rslt_attach_io1:
                self.a1_r1.fcu.DetachVolume(VolumeId=self.io1_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0])
                wait_volumes_state(self.a1_r1, volume_id_list=self.io1_volume_ids, state="available")
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T1077_standard_on_running_instance(self):
        self.rslt_attach_standard = self.a1_r1.fcu.AttachVolume(VolumeId=self.standard_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0],
                                                                Device="/dev/xvdb")

    def test_T1079_gp2_on_running_instance(self):
        self.rslt_attach_gp2 = self.a1_r1.fcu.AttachVolume(VolumeId=self.gp2_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0],
                                                           Device="/dev/xvdc")

    def test_T1081_io1_on_running_instance(self):
        self.rslt_attach_io1 = self.a1_r1.fcu.AttachVolume(VolumeId=self.io1_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0],
                                                           Device="/dev/xvdd")

    def test_T1078_standard_on_stopped_instance(self):
        self.rslt_attach_standard = self.a1_r1.fcu.AttachVolume(VolumeId=self.standard_volume_ids[0],
                                                                InstanceId=self.inst_info_stopped[INSTANCE_ID_LIST][0], Device="/dev/xvdb")

    def test_T1080_gp2_on_stopped_instance(self):
        self.rslt_attach_gp2 = self.a1_r1.fcu.AttachVolume(VolumeId=self.gp2_volume_ids[0],
                                                           InstanceId=self.inst_info_stopped[INSTANCE_ID_LIST][0], Device="/dev/xvdc")

    def test_T1082_io1_on_stopped_instance(self):
            self.rslt_attach_io1 = self.a1_r1.fcu.AttachVolume(VolumeId=self.io1_volume_ids[0],
                                                               InstanceId=self.inst_info_stopped[INSTANCE_ID_LIST][0], Device="/dev/xvdd")

    def test_T3953_incorrect_type_volume_id(self):
        vol_id = id_generator(size=8, chars=string.digits)
        try:
            self.rslt_attach_standard = self.a1_r1.fcu.AttachVolume(VolumeId=float(vol_id),
                                                                    InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdb")
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidVolumeID.Malformed", "Invalid ID received: {}. Expected format: vol-".format(float(vol_id)))

    def test_T3954_none_volume_id(self):
        try:
            self.rslt_attach_standard = self.a1_r1.fcu.AttachVolume(VolumeId=None,
                                                                    InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdb")
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', "The request must contain the parameter: volume")

    def test_T1089_with_nonexisting_volume_id(self):
        try:
            self.rslt_attach_standard = self.a1_r1.fcu.AttachVolume(VolumeId="vol-aaaaaaaa",
                                                                    InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdb")
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVolume.NotFound', "The volume 'vol-aaaaaaaa' does not exist.")

    def test_T3955_invalid_volume_id(self):
        try:
            self.rslt_attach_standard = self.a1_r1.fcu.AttachVolume(VolumeId="11a11a11",
                                                                    InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdb")
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVolumeID.Malformed', "Invalid ID received: 11a11a11. Expected format: vol-")

    def test_T1093_with_already_attached_volume_id(self):
        self.rslt_attach_standard = self.a1_r1.fcu.AttachVolume(VolumeId=self.standard_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0],
                                                                Device="/dev/xvdg")
        try:
            self.rslt_attach_standard = self.a1_r1.fcu.AttachVolume(VolumeId=self.standard_volume_ids[0],
                                                                    InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdc")
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, "VolumeInUse", "Volume '{}' is currently attached to instance: {}".format(self.standard_volume_ids[0],
                                                                                                               self.inst_info[INSTANCE_ID_LIST][0]))

    def test_T1092_with_already_used_device_name(self):
        self.rslt_attach_standard = self.a1_r1.fcu.AttachVolume(VolumeId=self.standard_volume_ids[0], InstanceId=self.inst_info[INSTANCE_ID_LIST][0],
                                                                Device="/dev/xvdj")
        try:
            self.rslt_attach_io1 = self.a1_r1.fcu.AttachVolume(VolumeId=self.io1_volume_ids[0],
                                                               InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdj")
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterValue",
                         "Attachment point is already in use for instance '{}': /dev/xvdj".format(self.inst_info[INSTANCE_ID_LIST][0]))

    def test_T1091_with_nionexisting_instance_id(self):
        try:
            self.rslt_attach_standard = self.a1_r1.fcu.AttachVolume(VolumeId=self.standard_volume_ids[0],
                                                                    InstanceId="i-aaaaaaaa", Device="/dev/xvdb")
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidInstanceID.NotFound", "The instance IDs do not exist: i-aaaaaaaa")

    def test_T3956_missing_device_name(self):
        try:
            self.rslt_attach_standard = self.a1_r1.fcu.AttachVolume(VolumeId=self.standard_volume_ids[0],
                                                                    InstanceId=self.inst_info[INSTANCE_ID_LIST][0])
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "The request must contain the parameter: device")

    def test_T1090_with_invalid_device_name(self):
        try:
            self.rslt_attach_standard = self.a1_r1.fcu.AttachVolume(VolumeId=self.standard_volume_ids[0],
                                                                    InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Device="invalid name")
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidBlockDeviceMapping", "Value for parameter 'Device' is not a valid BSU device name: invalid name")

    def test_T3957_from_another_account(self):
        try:
            self.rslt_attach_standard = self.a2_r1.fcu.AttachVolume(VolumeId=self.standard_volume_ids[0],
                                                                    InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Device="/dev/xvdb")
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidInstanceID.NotFound", "The instance IDs do not exist: {}".format(self.inst_info[INSTANCE_ID_LIST][0]))
