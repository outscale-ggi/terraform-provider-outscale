import pytest

from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import assert_dry_run
from qa_tina_tools.specs.check_tools import check_oapi_response


@pytest.mark.region_synchro_osu
@pytest.mark.region_osu
class Test_ReadImageExportTasks(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadImageExportTasks, cls).setup_class()
        cls.task_id = None
        # TODO needs osu support, create export tasks

    @classmethod
    def teardown_class(cls):
        super(Test_ReadImageExportTasks, cls).teardown_class()

    def test_T2826_valid_params(self):
        ret = self.a1_r1.oapi.ReadImageExportTasks().response
        check_oapi_response(ret, 'ReadImageExportTasksResponse')

    def test_T2827_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadImageExportTasks(DryRun=True)
        assert_dry_run(ret)

    def test_T3007_invalid_filters_task_ids(self):
        ret = self.a1_r1.oapi.ReadImageExportTasks(Filters={"TaskIds": ['abcd']}).response
        check_oapi_response(ret, 'ReadImageExportTasksResponse')

    def test_T3008_malformed_filters_task_ids(self):
        ret = self.a1_r1.oapi.ReadImageExportTasks(Filters={"TaskIds": ['image-export-123456']}).response
        check_oapi_response(ret, 'ReadImageExportTasksResponse')

    def test_T3009_unknown_filters_task_ids(self):
        ret = self.a1_r1.oapi.ReadImageExportTasks(Filters={"TaskIds": ['image-export-12345678']}).response
        check_oapi_response(ret, 'ReadImageExportTasksResponse')

    @pytest.mark.tag_sec_confidentiality
    def test_T3415_other_account(self):
        ret = self.a2_r1.oapi.ReadImageExportTasks().response.ImageExportTasks
        assert not ret

    @pytest.mark.tag_sec_confidentiality
    def test_T3416_other_account_with_filter(self):
        ret = self.a2_r1.oapi.ReadImageExportTasks(Filters={"TaskIds": ['abcd']}).response.ImageExportTasks
        assert not ret
