import pytest

from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import assert_dry_run
from qa_tina_tools.specs.oapi.check_tools import check_oapi_response


@pytest.mark.region_osu
class Test_ReadSnapshotExportTasks(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadSnapshotExportTasks, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ReadSnapshotExportTasks, cls).teardown_class()

    def test_T3005_empty_filters(self):
        ret = self.a1_r1.oapi.ReadSnapshotExportTasks().response
        check_oapi_response(ret, 'ReadSnapshotExportTasksResponse')

    def test_T3006_valid_param_dry_run(self):
        ret = self.a1_r1.oapi.ReadSnapshotExportTasks(DryRun=True)
        assert_dry_run(ret)

    def test_T3010_invalid_filters_task_ids(self):
        ret = self.a1_r1.oapi.ReadSnapshotExportTasks(Filters={"TaskIds": ['abcd']}).response
        check_oapi_response(ret, 'ReadSnapshotExportTasksResponse')

    def test_T3011_malformed_filters_task_ids(self):
        ret = self.a1_r1.oapi.ReadSnapshotExportTasks(Filters={"TaskIds": ['snap-export-123456']}).response
        check_oapi_response(ret, 'ReadSnapshotExportTasksResponse')

    def test_T3012_unknown_filters_task_ids(self):
        ret = self.a1_r1.oapi.ReadSnapshotExportTasks(Filters={"TaskIds": ['snap-export-12345678']}).response
        check_oapi_response(ret, 'ReadSnapshotExportTasksResponse')

    @pytest.mark.tag_sec_confidentiality
    def test_T3438_with_other_account(self):
        ret = self.a2_r1.oapi.ReadSnapshotExportTasks().response
        assert not ret.SnapshotExportTasks
