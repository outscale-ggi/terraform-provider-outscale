
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina import create_tools, wait_tools, info_keys, delete_tools


class Test_GetPasswordData(OscTestSuite):
    pass

    @classmethod
    def setup_class(cls):
        super(Test_GetPasswordData, cls).setup_class()
        cls.instance_info_a1 = None
        cls.instance_info_a2 = None
        try:
            cls.kp_info_a1 = create_tools.create_keypair(cls.a1_r1)
            cls.kp_info_a2 = create_tools.create_keypair(cls.a2_r1)
            cls.instance_info_a1 = create_tools.create_instances(cls.a1_r1, state=None, omi_id=cls.a1_r1.config.region._conf['windows_2016'],
                                                    inst_type='c4.large', key_name=cls.kp_info_a1[info_keys.NAME], nb=3)
            cls.instance_info_a2 = create_tools.create_instances(cls.a2_r1, state=None, omi_id=cls.a2_r1.config.region._conf['windows_2016'],
                                                    inst_type='c4.large', key_name=cls.kp_info_a2[info_keys.NAME])
            wait_tools.wait_instances_state(cls.a1_r1, cls.instance_info_a1[info_keys.INSTANCE_ID_LIST], state='ready', threshold=150)
            wait_tools.wait_instances_state(cls.a2_r1, cls.instance_info_a2[info_keys.INSTANCE_ID_LIST], state='ready', threshold=150)
        except Exception as error:
            try:
                cls.teardown_class()
            except:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.instance_info_a1:
                delete_tools.delete_instances(cls.a1_r1, cls.instance_info_a1)
            if cls.instance_info_a2:
                delete_tools.delete_instances(cls.a2_r1, cls.instance_info_a2)
            if cls.kp_info_a1:
                delete_tools.delete_keypair(cls.a1_r1, cls.kp_info_a1)
            if cls.kp_info_a2:
                delete_tools.delete_keypair(cls.a2_r1, cls.kp_info_a2)
        finally:
            super(Test_GetPasswordData, cls).teardown_class()

    def test_T4901_with_valid_params_with_an_other_account(self):
        try:
            self.a2_r1.fcu.GetPasswordData(InstanceId=self.instance_info_a1[info_keys.INSTANCE_ID_LIST][0])
        except OscApiException as error:
            misc.assert_error(error, 400, 'InvalidInstanceID.NotFound', 'The instance IDs do not exist: {}'.
                         format(self.instance_info_a1[info_keys.INSTANCE_ID_LIST][0]))
    #
    # def test_TXXX_with_incorrect_id(self):
    #     try:
    #         self.a1_r1.fcu.GetPasswordDataConsoleOutput(InstanceId='toto')
    #         assert False, "Call should not have been successful"
    #     except OscApiException as error:
    #         assert_error(error, 400, '', '')
    #
    # def test_TXXX_with_unknown_id(self):
    #     try:
    #         self.a1_r1.fcu.GetPasswordDataConsoleOutput(InstanceId='i-12345678')
    #         assert False, "Call should not have been successful"
    #     except OscApiException as error:
    #         assert_error(error, 400, '', '')
    #
    # def test_TXXX_with_incorrect_id_type(self):
    #     try:
    #         self.a1_r1.fcu.GetPasswordDataConsoleOutput(InstanceId=[self.instance_info_a1[INSTANCE_ID_LIST][0]])
    #         assert False, "Call should not have been successful"
    #     except OscApiException as error:
    #         assert_error(error, 400, '', '')
    #
    # @pytest.mark.tag_sec_confidentiality
    # def test_TXXX_with_id_of_other_account(self):
    #     try:
    #         self.a1_r1.fcu.GetPasswordDataConsoleOutput(InstanceId=[self.instance_info_a2[INSTANCE_ID_LIST][0]])
    #         assert False, 'Remove known error code'
    #     except OscApiException as error:
    #         assert_error(error, 400, '', '')
    #
    # def test_TXXX_with_terminated_instance(self):
    #     inst_id = self.instance_info_a1[INSTANCE_ID_LIST][1]
    #     terminate_instances(self.a1_r1, [inst_id])
    #     ret = self.a1_r1.fcu.GetPasswordDataConsoleOutput(InstanceId=inst_id)
    #     password = PKCS1_v1_5.new(RSA.importKey(open(self.kp_info[PATH]).read())).decrypt(
    #         base64.b64decode(ret.response.passwordData), None).decode("utf-8")
    #     assert password
    #
    # def test_TXXX_with_stopped_instance(self):
    #     inst_id = self.instance_info_a1[INSTANCE_ID_LIST][2]
    #     stop_instances(self.a1_r1, [inst_id])
    #     ret = self.a1_r1.fcu.GetPasswordDataConsoleOutput(InstanceId=inst_id)
    #     password = PKCS1_v1_5.new(RSA.importKey(open(self.kp_info[PATH]).read())).decrypt(
    #         base64.b64decode(ret.response.passwordData), None).decode("utf-8")
    #     assert password
