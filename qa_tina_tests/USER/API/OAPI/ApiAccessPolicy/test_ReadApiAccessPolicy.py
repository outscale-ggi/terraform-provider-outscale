import os

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_test_tools.compare_objects import verify_response
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from specs import check_oapi_error


class Test_ReadApiAccessPolicy(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_ReadApiAccessPolicy, cls).setup_class()

    def test_T5726_login_password(self):
        ret = self.a1_r1.oapi.ReadApiAccessPolicy(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword})
        ret.check_response()

    def test_T5997_login_password_incorrect(self):
        try:
            self.a1_r1.oapi.ReadApiAccessPolicy(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                                           osc_api.EXEC_DATA_LOGIN: 'foo', osc_api.EXEC_DATA_PASSWORD: 'bar'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4120)
            known_error('API-400', 'Incorrect error message')
            check_oapi_error(error, 1)

    def test_T5783_no_param(self):
        ret = self.a1_r1.oapi.ReadApiAccessPolicy()
        ret.check_response()
        self.logger.debug(ret.response.display())
        verify_response(ret.response, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_access_policy_no_param.json'), None)
