import pytest

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_sdk_common.exceptions.osc_exceptions import OscApiException


class Test_ReadAdminPassword(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadAdminPassword, cls).setup_class()
        cls.info = None
        try:
            cls.info = create_instances(cls.a1_r1, nb=2, state='running')
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            delete_instances(cls.a1_r1, cls.info)
        finally:
            super(Test_ReadAdminPassword, cls).teardown_class()

    def test_T2808_without_params(self):
        try:
            self.a1_r1.oapi.ReadAdminPassword()
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2809_with_valid_vm_id(self):
        self.a1_r1.oapi.ReadAdminPassword(VmId=self.info[INSTANCE_ID_LIST][0])

    def test_T2822_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadAdminPassword(VmId=self.info[INSTANCE_ID_LIST][1], DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3457_other_account(self):
        try:
            self.a2_r1.oapi.ReadAdminPassword(VmId=self.info[INSTANCE_ID_LIST][0])
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5063)
