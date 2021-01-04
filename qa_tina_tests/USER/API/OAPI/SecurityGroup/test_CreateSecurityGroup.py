# -*- coding:utf-8 -*-
from qa_test_tools.test_base import OscTestSuite
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_tina_tests.USER.API.OAPI.SecurityGroup.SecurityGroup import validate_sg


class Test_CreateSecurityGroup(OscTestSuite):

    def setup_method(self, method):
        super(Test_CreateSecurityGroup, self).setup_method(method)
        self.id = None

    def teardown_method(self, method):
        try:
            if self.id:
                self.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=self.id)
                self.id = None
        finally:
            super(Test_CreateSecurityGroup, self).teardown_method(method)
            self.id = None

    def test_T2715_without_param(self):
        try:
            ret = self.a1_r1.oapi.CreateSecurityGroup()
            self.id = ret.response.SecurityGroupId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2716_with_missing_description(self):
        try:
            ret = self.a1_r1.oapi.CreateSecurityGroup(SecurityGroupName='test_name')
            self.id = ret.response.SecurityGroupId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2717_with_missing_name(self):
        try:
            ret = self.a1_r1.oapi.CreateSecurityGroup(Description='test_desc')
            self.id = ret.response.SecurityGroupId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2718_with_all_param(self):
        ret = self.a1_r1.oapi.CreateSecurityGroup(Description="test_desc", SecurityGroupName="test_name")
        self.id = ret.response.SecurityGroup.SecurityGroupId
        ret.check_response()
        validate_sg(ret.response.SecurityGroup, expected_sg={'Description': 'test_desc', 'SecurityGroupName': 'test_name'})

    def test_T5135_with_incorrect_type_name(self):
        try:
            ret = self.a1_r1.oapi.CreateSecurityGroup(Description="test_desc", SecurityGroupName=["test", "name"])
            self.id = ret.response.SecurityGroupId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')
