import os

from qa_sdk_pub import osc_api
from qa_test_tools.compare_objects import verify_response
from qa_test_tools.test_base import OscTestSuite


class Test_ReadApiAccessPolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadApiAccessPolicy, cls).setup_class()

    def test_T5726_login_password(self):
        ret = self.a1_r1.oapi.ReadApiAccessPolicy(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword})
        ret.check_response()

    def test_T5783_no_param(self):
        ret = self.a1_r1.oapi.ReadApiAccessPolicy()
        ret.check_response()
        self.logger.debug(ret.response.display())
        verify_response(ret.response, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_access_policy_no_param.json'), None)