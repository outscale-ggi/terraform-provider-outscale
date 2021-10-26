
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_tina_tools.test_base import OscTinaTest
from specs import check_oapi_error


class Test_DeleteExportTask(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteExportTask, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteExportTask, cls).teardown_class()

    def test_T3027_empty_param(self):
        try:
            self.a1_r1.oapi.DeleteExportTask()
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T3028_invalid_export_task_id(self):
        try:
            self.a1_r1.oapi.DeleteExportTask(ExportTaskId='tata')
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='tata', prefixes='image-export-, snap-export-')

    def test_T3029_unknown_export_task_id(self):
        try:
            self.a1_r1.oapi.DeleteExportTask(ExportTaskId='image-export-12345678')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5058')
        try:
            self.a1_r1.oapi.DeleteExportTask(ExportTaskId='snap-copy-12345678')
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='snap-copy-12345678', prefixes='snap-export-, image-export-')
        try:
            self.a1_r1.oapi.DeleteExportTask(ExportTaskId='snap-export-12345678')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5058')

    def test_T3030_malformed_export_task_id(self):
        try:
            self.a1_r1.oapi.DeleteExportTask(ExportTaskId='image-export-1234567')
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='image-export-1234567')
        try:
            self.a1_r1.oapi.DeleteExportTask(ExportTaskId='snap-copy-123456789')
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='snap-copy-123456789', prefixes='image-export-, snap-export-')
        try:
            self.a1_r1.oapi.DeleteExportTask(ExportTaskId='snap-export-1234')
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='snap-export-1234')
