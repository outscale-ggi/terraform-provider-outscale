from qa_sdk_pub import osc_api
from qa_test_tools.test_base import OscTestSuite

class Test_UpdateApiAccessPolicy(OscTestSuite):

    def test_T5727_login_password(self):
        ret = self.a1_r1.oapi.UpdateApiAccessPolicy(
            exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword},
            MaxAccessKeyExpirationSeconds=36000000, RequireTrustedEnv=False)
        ret.check_response()

    # TODO PQA-3036: <global> Add all others tests with ak/sk authentication
    # TODO PQA-3036: /!\ when update succeed with RequireTrustedEnv=True MFA authent will be required for teardown
    # TODO PQA-3036:     (re-set with RequireTrustedEnv=False with MFA authent)
    # TODO PQA-3036: Add tests:
    # TODO PQA-3036:  - with dry run ==> ok
    # TODO PQA-3036:  - without MaxAccessKeyExpirationSeconds ==> ko
    # TODO PQA-3036:  - without RequireTrustedEnv ==> ko
    # TODO PQA-3036:  - with invalid MaxAccessKeyExpirationSeconds ==> ko
    # TODO PQA-3036:  - with invalid RequireTrustedEnv ==> ko
    # TODO PQA-3036:  - (valid functional) with RequireTrustedEnv=True (setup: need ApiAccessRule with CA and ak/sk with expiration date) ==> ok
    # TODO PQA-3036:  - with RequireTrustedEnv=True and without ApiAccessRule ==> ko
    # TODO PQA-3036:  - with RequireTrustedEnv=True and with ApiAccessRule without CA (rule based only on IP) ==> ko
    # TODO PQA-3036:  - with RequireTrustedEnv=True and with ak/sk without expiration date ==> ko
