from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tools.tools.tina import create_tools
from qa_tina_tests.USER.API.OAPI.ApiAccessRule.ApiAccessRule import ApiAccessRule
from qa_sdk_common.exceptions.osc_exceptions import OscApiException

#    CreateApiAccessRuleRequest:
#      additionalProperties: false
#      properties:
#        CaIds:
#          description: CreateApiAccessRuleRequest_CaIds
#          items:
#            type: string
#          type: array
#        Cns:
#          description: CreateApiAccessRuleRequest_Cns
#          items:
#            type: string
#          type: array
#        Description:
#          description: CreateApiAccessRuleRequest_Description
#          type: string
#        DryRun:
#          description: CreateApiAccessRuleRequest_DryRun
#          type: boolean
#        IpRanges:
#          description: CreateApiAccessRuleRequest_IpRanges
#          items:
#            type: string
#          type: array
#      type: object

class Test_CreateApiAccessRule(ApiAccessRule):
    
    def test_T5247_only_description(self):
        try:
            self.osc_sdk.oapi.CreateApiAccessRule(Description='description')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4118')

    def test_T5248_all_params(self):
        ret = self.osc_sdk.oapi.CreateApiAccessRule(Description='description', CaIds=self.ca_ids,
                                                   Cns=[create_tools.CLIENT_CERT_CN1, create_tools.CLIENT_CERT_CN2], IpRanges=["1.1.1.1/32", "2.2.2.2/32"])
        ret.check_response()

    def test_T5249_only_ca_ids(self):
        ret = self.osc_sdk.oapi.CreateApiAccessRule(Description='description', CaIds=self.ca_ids)
        ret.check_response()

    def test_T5250_only_cns(self):
        try:
            self.osc_sdk.oapi.CreateApiAccessRule(Description='description', Cns=[create_tools.CLIENT_CERT_CN1, create_tools.CLIENT_CERT_CN2])
        except Exception as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4118')

    def test_T5251_only_ip_ranges(self):
        ret = self.osc_sdk.oapi.CreateApiAccessRule(Description='description', IpRanges=["1.1.1.1/32", "2.2.2.2/32"])
        ret.check_response()

    def test_T5252_incorrect_description(self):
        try:
            self.osc_sdk.oapi.CreateApiAccessRule(Description=None, CaIds=self.ca_ids,
                                                Cns=[create_tools.CLIENT_CERT_CN1, create_tools.CLIENT_CERT_CN2], IpRanges=["1.1.1.1/32", "2.2.2.2/32"]).response
            assert False, 'Call should not have been successful'
        except Exception as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5253_incorrect_ca_ids(self):
        try:
            self.osc_sdk.oapi.CreateApiAccessRule(Description='description', CaIds=['ca-1', 'ca-2'],
                                                Cns=[create_tools.CLIENT_CERT_CN1, create_tools.CLIENT_CERT_CN2], IpRanges=["1.1.1.1/32", "2.2.2.2/32"]).response
            assert False, 'Call should not have been successful'
        except Exception as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4122')

    def test_T5254_incorrect_ip_ranges(self):
        try:
            self.osc_sdk.oapi.CreateApiAccessRule(Description='description', CaIds=self.ca_ids,
                                                Cns=[create_tools.CLIENT_CERT_CN1, create_tools.CLIENT_CERT_CN2], IpRanges=["1.1.1/32", "2.2.2.2/32"]).response
            assert False, 'Call should not have been successful'
        except Exception as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4118')

    def test_T5255_incorrect_ca_ids_type(self):
        try:
            self.osc_sdk.oapi.CreateApiAccessRule(Description='description', CaIds=self.ca_ids[0],
                                                Cns=[create_tools.CLIENT_CERT_CN1, create_tools.CLIENT_CERT_CN2], IpRanges=["1.1.1.1/32", "2.2.2.2/32"]).response
            assert False, 'Call should not have been successful'
        except Exception as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5256_incorrect_cns_type(self):
        try:
            self.osc_sdk.oapi.CreateApiAccessRule(Description='description', CaIds=self.ca_ids,
                                                Cns=create_tools.CLIENT_CERT_CN1, IpRanges=["1.1.1.1/32", "2.2.2.2/32"])
            assert False, 'Call should not have been successful'
        except Exception as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5257_incorrect_ip_ranges_type(self):
        try:
            self.osc_sdk.oapi.CreateApiAccessRule(Description='description', CaIds=self.ca_ids,
                                                Cns=[create_tools.CLIENT_CERT_CN1, create_tools.CLIENT_CERT_CN2], IpRanges="1.1.1.1/32")
            assert False, 'Call should not have been successful'
        except Exception as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5258_dry_run(self):
        ret = self.osc_sdk.oapi.CreateApiAccessRule(Description='description', CaIds=self.ca_ids,
                                                   Cns=[create_tools.CLIENT_CERT_CN1, create_tools.CLIENT_CERT_CN2], IpRanges=["1.1.1.1/32", "2.2.2.2/32"], DryRun=True)
        assert_dry_run(ret)
