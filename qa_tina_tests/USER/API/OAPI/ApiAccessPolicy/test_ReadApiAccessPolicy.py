from qa_test_tools.test_base import OscTestSuite
from qa_sdk_pub import osc_api


class Test_ReadApiAccessPolicy(OscTestSuite):

    def test_T5726_login_password(self):
        ret = self.a1_r1.oapi.ReadApiAccessPolicy(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword})
        ret.check_response()
