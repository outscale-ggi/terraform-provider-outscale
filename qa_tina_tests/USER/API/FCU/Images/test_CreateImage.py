from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.wait_tools import wait_images_state, wait_instances_state
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_test_tools.misc import assert_error, id_generator
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
import string


class Test_CreateImage(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateImage, cls).setup_class()
        cls.inst_info = None
        try:
            cls.inst_info = create_instances(cls.a1_r1, state="running")
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
        finally:
            super(Test_CreateImage, cls).teardown_class()

    # parameter Name constraints
    # AWS ==>3-128 alphanumeric characters, parentheses (()), square brackets ([]), spaces ( ), periods (.), slashes (/), dashes (-), single quotes ('), at-signs (@), or underscores(_)
    # TINA ==> [a-zA-Z0-9_ ()/.-] , length: (3, 128)

    def test_T2279_name_too_short(self):
        name = 'a' * 2
        img_id = None
        try:
            img_id = self.a1_r1.fcu.CreateImage(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Name=name).response.imageId
        except OscApiException as err:
            assert_error(err, 400, 'InvalidAMIName.Malformed', 'AMI name received: ' + name + '. Constraints: [a-zA-Z0-9_ ()/.-], length: (3, 128)')
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)

    def test_T2281_name_min_length(self):
        name = 'a' * 3
        img_id = None
        try:
            img_id = self.a1_r1.fcu.CreateImage(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Name=name).response.imageId
            wait_images_state(osc_sdk=self.a1_r1, image_id_list=[img_id], state='available')
            wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=self.inst_info[INSTANCE_ID_LIST], state='running')
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)

    def test_T2282_name_max_length(self):
        name = 'a' * 128
        img_id = None
        try:
            img_id = self.a1_r1.fcu.CreateImage(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Name=name).response.imageId
            wait_images_state(osc_sdk=self.a1_r1, image_id_list=[img_id], state='available')
            wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=self.inst_info[INSTANCE_ID_LIST], state='running')
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)

    def test_T2280_name_too_long(self):
        name = 'a' * 129
        img_id = None
        try:
            img_id = self.a1_r1.fcu.CreateImage(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Name=name).response.imageId
        except OscApiException as err:
            assert_error(err, 400, 'InvalidAMIName.Malformed', 'AMI name received: ' + name + '. Constraints: [a-zA-Z0-9_ ()/.-], length: (3, 128)')
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)

    def test_T2283_name_incorrect_charset(self):
        name = 'é!àçè'
        img_id = None
        try:
            img_id = self.a1_r1.fcu.CreateImage(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Name=name).response.imageId
        except OscApiException as err:
            assert_error(err, 400, 'InvalidAMIName.Malformed', 'AMI name received: é!àçè. Constraints: [a-zA-Z0-9_ ()/.-], length: (3, 128)')
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)

    def test_T2284_name_correct_charset(self):
        name = 'azertyuiopqsdfghjklmwxcvbn0123456789AZERTYUIOPQSDFGHJKLMWXCVBN_ ()/.-'
        img_id = None
        try:
            img_id = self.a1_r1.fcu.CreateImage(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Name=name).response.imageId
            wait_images_state(osc_sdk=self.a1_r1, image_id_list=[img_id], state='available')
            wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=self.inst_info[INSTANCE_ID_LIST], state='running')
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)

    def test_T3917_with_stopped_instance(self):
        name = 'a' * 3
        img_id = None
        try:
            self.a1_r1.fcu.StopInstances(InstanceId=self.inst_info[INSTANCE_ID_LIST], Force=True)
            wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=self.inst_info[INSTANCE_ID_LIST], state='stopped')
            img_id = self.a1_r1.fcu.CreateImage(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Name=name).response.imageId
            wait_images_state(osc_sdk=self.a1_r1, image_id_list=[img_id], state='available')
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)
            self.a1_r1.fcu.StartInstances(InstanceId=self.inst_info[INSTANCE_ID_LIST])
            wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=self.inst_info[INSTANCE_ID_LIST], state='running')
            
    def test_T4077_check_img_id_start_with_ami(self):
        try:
            img_name = id_generator(prefix="omi-", size=8, chars=string.ascii_lowercase)
            img_id = self.a1_r1.fcu.CreateImage(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Name=img_name).response.imageId
            assert img_id.lower().startswith('ami-'), "Image ID should start with 'ami-"
        finally:
            self.a1_r1.fcu.DeregisterImage(ImageId=img_id)
