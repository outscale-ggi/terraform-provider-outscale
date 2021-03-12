
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.tools.tina import create_tools
from qa_test_tools.misc import compare_validate_objects, assert_dry_run, assert_oapi_error
from qa_test_tools.test_base import known_error
from qa_tina_tests.USER.API.OAPI.ApiAccessRule.ApiAccessRule import ApiAccessRule


class Test_UpdateApiAccessRule(ApiAccessRule):

    @classmethod
    def setup_class(cls):
        cls.api_access_rule = None
        super(Test_UpdateApiAccessRule, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_UpdateApiAccessRule, cls).teardown_class()

    def my_setup(self):
        self.api_access_rule = None
        resp = self.osc_sdk.oapi.CreateApiAccessRule(Description='description', CaIds=self.ca_ids,
                                                     Cns=[create_tools.CLIENT_CERT_CN1, create_tools.CLIENT_CERT_CN2],
                                                     IpRanges=["1.1.1.1/32", "2.2.2.2/32"]).response
        self.api_access_rule = resp.ApiAccessRule

    def teardown_method(self, method):
        try:
            if self.api_access_rule:
                self.osc_sdk.oapi.DeleteApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId)
        except:
            pass
        finally:
            ApiAccessRule.teardown_method(self, method)

    def test_T5280_no_params(self):
        self.my_setup()
        try:
            self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4118')

    def test_T5281_same_description(self):
        self.my_setup()
        try:
            self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId, Description='description')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4118')

    def test_T5282_same_ca_ids(self):
        self.my_setup()
        ret = self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId, CaIds=self.ca_ids)
        ret.check_response()
        try:
            compare_validate_objects(self.api_access_rule, ret.response.ApiAccessRule)
            raise OscApiException
        except AssertionError:
            known_error('GTW-1544', 'Missing elements in response.')

    def test_T5283_two_same(self):
        self.my_setup()
        ret = self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId,
                                                    CaIds=self.ca_ids, Description='description')
        ret.check_response()
        try:
            compare_validate_objects(self.api_access_rule, ret.response.ApiAccessRule)
            raise OscApiException
        except AssertionError:
            known_error('GTW-1544', 'Missing elements in response.')

    def test_T5284_one_same_one_diff(self):
        self.my_setup()
        ret = self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId,
                                                    CaIds=self.ca_ids, Description='descriptionbis')
        ret.check_response()
        try:
            compare_validate_objects(self.api_access_rule, ret.response.ApiAccessRule, Description='descriptionbis')
            raise OscApiException
        except AssertionError:
            known_error('GTW-1544', 'Missing elements in response.')

    def test_T5285_one_diff_one_same(self):
        self.my_setup()
        ret = self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId,
                                                    CaIds=self.ca_ids[0:1], Description='description')
        ret.check_response()
        try:
            compare_validate_objects(self.api_access_rule, ret.response.ApiAccessRule, CaIds=self.ca_ids[0:1])
            raise OscApiException
        except AssertionError:
            known_error('GTW-1544', 'Missing elements in response.')

    def test_T5286_update_ca_ids(self):
        self.my_setup()
        ret = self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId, CaIds=self.ca_ids[0:1])
        ret.check_response()
        try:
            compare_validate_objects(self.api_access_rule, ret.response.ApiAccessRule, CaIds=self.ca_ids[0:1])
            raise OscApiException
        except AssertionError:
            known_error('GTW-1544', 'Missing elements in response.')

    def test_T5287_update_cns(self):
        self.my_setup()
        ret = self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId,
                                                    CaIds=self.ca_ids[0:1], Cns=[create_tools.CLIENT_CERT_CN1])
        ret.check_response()
        try:
            compare_validate_objects(self.api_access_rule, ret.response.ApiAccessRule, CaIds=self.ca_ids[0:1], Cns=[create_tools.CLIENT_CERT_CN1])
            raise OscApiException
        except AttributeError:
            known_error('GTW-1544', 'Missing elements in response.')

    def test_T5288_update_description(self):
        self.my_setup()
        try:
            ret = self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId,
                                                        Description='NewDescription', IpRanges=["1.1.1.1/32", "2.2.2.2/32"])
            ret.check_response()
            compare_validate_objects(self.api_access_rule, ret.response.ApiAccessRule,
                                     Description='NewDescription', IpRanges=["1.1.1.1/32", "2.2.2.2/32"])
            raise OscApiException
        except AssertionError:
            known_error('GTW-1544', 'Could not update description')

    def test_T5289_update_ip_ranges(self):
        self.my_setup()
        ret = self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId, IpRanges=["1.1.1.1/32"])
        ret.check_response()
        try:
            compare_validate_objects(self.api_access_rule, ret.response.ApiAccessRule, IpRanges=["1.1.1.1/32"])
            raise OscApiException
        except AssertionError:
            known_error('GTW-1544', 'Missing elements in response.')

    def test_T5290_all_items(self):
        self.my_setup()
        ret = self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId,
                                                     CaIds=self.ca_ids[0:1],
                                                     Cns=[create_tools.CLIENT_CERT_CN1],
                                                     Description='NewDescription',
                                                     IpRanges=["1.1.1.1/32"])
        ret.check_response()
        compare_validate_objects(self.api_access_rule, ret.response.ApiAccessRule,
                                 CaIds=self.ca_ids[0:1],
                                 Cns=[create_tools.CLIENT_CERT_CN1],
                                 Description='NewDescription',
                                 IpRanges=["1.1.1.1/32"])

    def test_T5291_update_incorrect_ca_ids(self):
        self.my_setup()
        try:
            self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId, CaIds="foobar")
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5292_update_incorrect_cns(self):
        self.my_setup()
        try:
            self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId, Cns=create_tools.CLIENT_CERT_CN1)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5293_update_incorrect_description(self):
        self.my_setup()
        try:
            self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId, Description=['NewDescription'])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5294_update_incorrect_ip_ranges(self):
        self.my_setup()
        try:
            self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId, IpRanges="1.1.1.1/32")
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5295_dry_run(self):
        self.my_setup()
        ret = self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId, Description='NewDescription', DryRun=True)
        assert_dry_run(ret)

    def test_T5296_incorrect_rule_id(self):
        try:
            self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId="foobar", Description='NewDescription')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4118')

    def test_T5297_unknown_rule_id(self):
        try:
            self.osc_sdk.oapi.UpdateApiAccessRule(ApiAccessRuleId="aar-12345678", Description='NewDescription')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4118')

    def test_T5298_other_account(self):
        self.my_setup()
        try:
            self.a2_r1.oapi.UpdateApiAccessRule(ApiAccessRuleId=self.api_access_rule.ApiAccessRuleId, Description='NewDescription')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4118')
