
import os

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from specs import check_oapi_error
from qa_test_tools.compare_objects import verify_response, create_hints
from qa_tina_tools.test_base import OscTinaTest


class Test_CreateSecurityGroup(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.sg_id = None
        super(Test_CreateSecurityGroup, cls).setup_class()

    def setup_method(self, method):
        super(Test_CreateSecurityGroup, self).setup_method(method)
        self.sg_id = None

    def teardown_method(self, method):
        try:
            if self.sg_id:
                self.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=self.sg_id)
                self.sg_id = None
        finally:
            super(Test_CreateSecurityGroup, self).teardown_method(method)
            self.sg_id = None

    def test_T2715_without_param(self):
        try:
            ret = self.a1_r1.oapi.CreateSecurityGroup()
            self.sg_id = ret.response.SecurityGroupId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T2716_with_missing_description(self):
        try:
            ret = self.a1_r1.oapi.CreateSecurityGroup(SecurityGroupName='test_name')
            self.sg_id = ret.response.SecurityGroupId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T2717_with_missing_name(self):
        try:
            ret = self.a1_r1.oapi.CreateSecurityGroup(Description='test_desc')
            self.sg_id = ret.response.SecurityGroupId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T2718_with_all_param(self):
        ret = self.a1_r1.oapi.CreateSecurityGroup(Description="test_desc", SecurityGroupName="test_name")
        self.sg_id = ret.response.SecurityGroup.SecurityGroupId
        ret.check_response()
        hints = create_hints([self.sg_id, self.a1_r1.config.account.account_id, 'test_desc', 'test_name'])
        verify_response(ret.response, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'create_all_params.json'), hints)

    def test_T5135_with_incorrect_type_name(self):
        try:
            ret = self.a1_r1.oapi.CreateSecurityGroup(Description="test_desc", SecurityGroupName=["test", "name"])
            self.sg_id = ret.response.SecurityGroupId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4110)
