# -*- coding:utf-8 -*-
import os
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.compare_objects import verify_response


class Test_DeleteSecurityGroup(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.sg_id = None
        super(Test_DeleteSecurityGroup, cls).setup_class()

    def setup_method(self, method):
        super(Test_DeleteSecurityGroup, self).setup_method(method)
        try:
            self.sg_id = self.a1_r1.oapi.CreateSecurityGroup(Description="test_desc",
                                                          SecurityGroupName="test_delete").response.SecurityGroup.SecurityGroupId
        except:
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.sg_id:
                self.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=self.sg_id)
        finally:
            super(Test_DeleteSecurityGroup, self).teardown_method(method)

    def test_T2732_without_param(self):
        try:
            ret = self.a1_r1.oapi.DeleteSecurityGroup()
            self.sg_id = ret.response.SecurityGroup.SecurityGroupId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2733_with_wrong_id(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId='1234')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2734_with_wrong_name(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupName='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5020')

    def test_T2735_with_id(self):
        ret = self.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=self.sg_id)
        self.sg_id = None
        ret.check_response()
        assert verify_response(ret.response, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                          'delete_with_id.json'), None), 'Could not verify response content.'

    def test_T2736_with_name(self):
        ret = self.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupName='test_delete')
        self.sg_id = None
        ret.check_response()
        assert verify_response(ret.response, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                          'delete_with_name.json'), None), 'Could not verify response content.'

    @pytest.mark.tag_sec_confidentiality
    def test_T3515_with_other_user(self):
        try:
            self.a2_r1.oapi.DeleteSecurityGroup(SecurityGroupName='test_delete')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5020')

    def test_T3516_valid_dry_run(self):
        ret = self.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupName='test_delete', DryRun=True)
        assert_dry_run(ret)
