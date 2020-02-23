from qa_common_tools.misc import assert_error
from qa_common_tools.test_base import OscTestSuite, known_error
from osc_common.exceptions.osc_exceptions import OscApiException

DEVICE = '/dev/xvdc'
MOUNT_DIR = 'mountdir'
SIZE_GB = 500


class Test_find(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_find, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_find, cls).teardown_class()

    def test_T2286_no_params(self):
        ret = None
        try:
            ret = self.a1_r1.intel.task.find()
        except OscApiException as error:
            assert_error(error, 200, -32603, 'Internal error.')
        if ret:
            for res in ret.response.result:
                assert res.start_date
                assert res.state == 'active' or res.state == 'pending' or res.completion_date
