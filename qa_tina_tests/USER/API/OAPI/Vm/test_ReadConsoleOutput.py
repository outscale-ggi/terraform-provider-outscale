import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from specs import check_oapi_error
from qa_test_tools.misc import assert_dry_run
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST


class Test_ReadConsoleOutput(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_ReadConsoleOutput, cls).setup_class()
        cls.info = None
        try:
            cls.info = create_instances(cls.a1_r1, nb=2, state='running')
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.info:
                # ret = cls.a1_r1.oapi.ReadVms(Filters={'VmIds': cls.info[INSTANCE_ID_LIST]}).response.Vms
                # cls.info[INSTANCE_ID_LIST] = [inst.VmId for inst in ret]
                delete_instances(cls.a1_r1, cls.info)
        finally:
            super(Test_ReadConsoleOutput, cls).teardown_class()

    def test_T2824_valid_params(self):
        ret = self.a1_r1.oapi.ReadConsoleOutput(VmId=self.info[INSTANCE_ID_LIST][0])
        ret.check_response()

    def test_T2825_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadConsoleOutput(VmId=self.info[INSTANCE_ID_LIST][0], DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3458_other_account(self):
        try:
            self.a2_r1.oapi.ReadConsoleOutput(VmId=self.info[INSTANCE_ID_LIST][0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5063, id=self.info[INSTANCE_ID_LIST][0])
