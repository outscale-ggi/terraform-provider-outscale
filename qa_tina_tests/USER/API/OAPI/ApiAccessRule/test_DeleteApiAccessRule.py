from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.tools.tina import create_tools
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tests.USER.API.OAPI.ApiAccessRule.ApiAccessRule import ApiAccessRule


class Test_DeleteApiAccessRule(ApiAccessRule):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteApiAccessRule, cls).setup_class()
        cls.api_access_rule_id = None

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteApiAccessRule, cls).teardown_class()

    def my_setup(self):
        self.api_access_rule_id = None
        resp = self.osc_sdk.oapi.CreateApiAccessRule(
            Description='description', CaIds=self.ca_ids,
            Cns=[create_tools.CLIENT_CERT_CN1, create_tools.CLIENT_CERT_CN2], IpRanges=["1.1.1.1/32", "2.2.2.2/32"]).response
        self.api_access_rule_id = resp.ApiAccessRule.ApiAccessRuleId

    def teardown_method(self, method):
        try:
            if self.api_access_rule_id:
                self.osc_sdk.oapi.DeleteApiAccessRule(ApiAccessRuleId=self.api_access_rule_id)
        except:
            pass
        finally:
            ApiAccessRule.teardown_method(self, method)

    def test_T5259_valid_params(self):
        self.my_setup()
        ret = self.osc_sdk.oapi.DeleteApiAccessRule(ApiAccessRuleId=self.api_access_rule_id)
        ret.check_response()

    def test_T5260_unknown_id(self):
        try:
            self.osc_sdk.oapi.DeleteApiAccessRule(ApiAccessRuleId='ca-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4118')

    def test_T5261_invalid_id(self):
        try:
            self.osc_sdk.oapi.DeleteApiAccessRule(ApiAccessRuleId='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4118')

    def test_T5262_invalid_id_type(self):
        self.my_setup()
        try:
            self.osc_sdk.oapi.DeleteApiAccessRule(ApiAccessRuleId=[self.api_access_rule_id])
            self.api_access_rule_id = None
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5263_other_account(self):
        self.my_setup()
        try:
            self.a2_r1.oapi.DeleteApiAccessRule(ApiAccessRuleId=self.api_access_rule_id)
            self.api_access_rule_id = None
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4122')

    def test_T5264_dry_run(self):
        self.my_setup()
        ret = self.osc_sdk.oapi.DeleteApiAccessRule(ApiAccessRuleId=self.api_access_rule_id, DryRun=True)
        assert_dry_run(ret)
