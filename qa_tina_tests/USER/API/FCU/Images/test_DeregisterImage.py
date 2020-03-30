from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_test_tools.misc import id_generator, assert_error
import string
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
import pytest


class Test_DeregisterImage(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeregisterImage, cls).setup_class()
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
            super(Test_DeregisterImage, cls).teardown_class()
    
    def test_T1543_test_delete_image(self):
        img_name = id_generator(prefix="omi-", size=8, chars=string.ascii_lowercase)
        img_id = self.a1_r1.fcu.CreateImage(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Name=img_name).response.imageId
        ret = self.a1_r1.fcu.DeregisterImage(ImageId=img_id)
        assert ret.response.osc_return

    def test_T4078_none_image_id(self):
        try:
            self.a1_r1.fcu.DeregisterImage(ImageId=None)
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidAMIID.Malformed", "Invalid id: 'None' (expecting 'ami-...')")

    def test_T4079_empty_image_id(self):
        try:
            self.a1_r1.fcu.DeregisterImage(ImageId="")
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidAMIID.Malformed", "Invalid id: '' (expecting 'ami-...')")

    @pytest.mark.tag_sec_confidentiality
    def test_T4080_with_another_account(self):
        img_name = id_generator(prefix="omi-", size=8, chars=string.ascii_lowercase)
        img_id = self.a1_r1.fcu.CreateImage(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], Name=img_name).response.imageId
        try:
            self.a2_r1.fcu.DeregisterImage(ImageId=img_id)
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "AuthFailure", "Not authorized for image:{}".format(img_id))
        finally:
            self.a1_r1.fcu.DeregisterImage(ImageId=img_id)
