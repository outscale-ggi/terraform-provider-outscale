from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite, assert_code
from qa_tina_tools.tools.tina import info_keys
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_images
from qa_tina_tools.tools.tina.create_tools import create_instances, create_image
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old


class Test_add_permissions(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_add_permissions, cls).setup_class()
        cls.inst_id = None
        cls.image_id = None

        cls.inst_info = create_instances(cls.a1_r1)
        cls.inst_id = cls.inst_info[info_keys.INSTANCE_ID_LIST][0]
        _, cls.image_id = create_image(cls.a1_r1, cls.inst_id, state='available')

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_id:
                delete_instances_old(cls.a1_r1, [cls.inst_info])
            if cls.image_id:
                cleanup_images(cls.a1_r1, image_id_list=[cls.image_id], force=True)
        except Exception as error:
            cls.logger.exception(error)
        finally:
            super(Test_add_permissions, cls).teardown_class()

    def test_T5124_with_str_type_for_users(self):
        try:
            self.a1_r1.intel.image.add_permissions(owner=self.a1_r1.config.account.account_id, image=self.image_id, users='toto')
            assert False, 'Call should Fail, invalid type parameter'

        except OscApiException as error:
            assert_code(error, 200, "invalid-parameter-type - Value of parameter 'Users' must be of type: list." \
                                    " \n 'Received: [arg0.users]'")

    def test_T5125_with_valid_type_for_users(self):
        actual_user = self.a1_r1.config.account.account_id
        self.a1_r1.intel.image.add_permissions(owner=self.a1_r1.config.account.account_id, image=self.image_id, users=[actual_user])
        assert True
