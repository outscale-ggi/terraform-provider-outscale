from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.tools.tina import create_tools
from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_tina_tests.USER.API.OAPI.ApiAccessRule.ApiAccessRule import ApiAccessRule


class Test_ReadApiAccessRules(ApiAccessRule):

    @classmethod
    def setup_class(cls):
        super(Test_ReadApiAccessRules, cls).setup_class()
        cls.api_access_rule_ids = []
        try:
            cls.api_access_rule_ids.append(
                cls.osc_sdk.oapi.CreateApiAccessRule(Description='description_1', CaIds=cls.ca_ids[0:1],
                                                     Cns=[create_tools.CLIENT_CERT_CN1],
                                                     IpRanges=["1.1.1.1/32"]).response.ApiAccessRule.ApiAccessRuleId)
            cls.api_access_rule_ids.append(
                cls.osc_sdk.oapi.CreateApiAccessRule(Description='description_2', CaIds=cls.ca_ids[1:3],
                                                     Cns=[create_tools.CLIENT_CERT_CN1],
                                                     IpRanges=["1.1.1.1/32", "2.2.2.2/32"]).response.ApiAccessRule.ApiAccessRuleId)
            cls.api_access_rule_ids.append(
                cls.osc_sdk.oapi.CreateApiAccessRule(Description='description_3', CaIds=cls.ca_ids[2:3],
                                                     Cns=[create_tools.CLIENT_CERT_CN2],
                                                     IpRanges=["2.2.2.2/32"]).response.ApiAccessRule.ApiAccessRuleId)
            cls.api_access_rule_ids.append(
                cls.osc_sdk.oapi.CreateApiAccessRule(Description='description_4', CaIds=cls.ca_ids,
                                                     Cns=[create_tools.CLIENT_CERT_CN2],
                                                     IpRanges=["1.1.1.1/32", "2.2.2.2/32", "3.3.3.3/32"]).response.ApiAccessRule.ApiAccessRuleId)
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            for api_access_rule_id in cls.api_access_rule_ids:
                cls.osc_sdk.oapi.DeleteApiAccessRule(ApiAccessRuleId=api_access_rule_id)
        finally:
            super(Test_ReadApiAccessRules, cls).teardown_class()

    def test_T5267_no_params(self):
        ret = self.osc_sdk.oapi.ReadApiAccessRules()
        ret.check_response()
        assert len(ret.response.ApiAccessRules) == 6

    def test_T5268_extra_param(self):
        try:
            self.osc_sdk.oapi.ReadApiAccessRules(Foo='Bar')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T5269_filter_rule_ids(self):
        resp = self.osc_sdk.oapi.ReadApiAccessRules(Filters={'ApiAccessRuleIds': self.api_access_rule_ids[1:3]}).response
        assert len(resp.ApiAccessRules) == 2

    def test_T5270_filter_ca_ids(self):
        resp = self.osc_sdk.oapi.ReadApiAccessRules(Filters={'CaIds': self.ca_ids[0:1]}).response
        assert len(resp.ApiAccessRules) == 2

    def test_T5271_filter_cns(self):
        resp = self.osc_sdk.oapi.ReadApiAccessRules(Filters={'Cns': [create_tools.CLIENT_CERT_CN2]}).response
        assert len(resp.ApiAccessRules) == 2

    def test_T5272_filter_descriptions(self):
        resp = self.osc_sdk.oapi.ReadApiAccessRules(Filters={'Descriptions': ['description_2']}).response
        assert len(resp.ApiAccessRules) == 1

    def test_T5273_filter_ip_ranges(self):
        resp = self.osc_sdk.oapi.ReadApiAccessRules(Filters={'IpRanges': ["1.1.1.1/32", "4.4.4.4/32"]}).response
        assert len(resp.ApiAccessRules) == 3

    def test_T5274_filter_incorrect_type_rule_ids(self):
        try:
            self.osc_sdk.oapi.ReadApiAccessRules(Filters={'ApiAccessRuleIds': self.api_access_rule_ids[1]})
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5275_filter_incorrect_type_ca_ids(self):
        try:
            self.osc_sdk.oapi.ReadApiAccessRules(Filters={'CaIds': self.ca_ids[0]})
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5276_filter_incorrect_type_cns(self):
        try:
            self.osc_sdk.oapi.ReadApiAccessRules(Filters={'Cns': create_tools.CLIENT_CERT_CN2})
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5277_filter_incorrect_type_descriptions(self):
        try:
            self.osc_sdk.oapi.ReadApiAccessRules(Filters={'Descriptions': 'description_2'})
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5278_filter_incorrect_type_ip_ranges(self):
        try:
            self.osc_sdk.oapi.ReadApiAccessRules(Filters={'IpRanges': "1.1.1.1/32"})
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5279_dry_run(self):
        ret = self.osc_sdk.oapi.ReadApiAccessRules(DryRun=True)
        assert_dry_run(ret)
