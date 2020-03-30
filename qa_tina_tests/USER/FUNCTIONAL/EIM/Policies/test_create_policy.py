from qa_test_tools.test_base import OscTestSuite
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator, assert_oapi_error
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
import pytest


class Test_create_policy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create_policy, cls).setup_class()
        cls.user_info = None
        cls.account_sdk = None
        cls.accesskey_info = None

    @classmethod
    def teardown_class(cls):
        super(Test_create_policy, cls).teardown_class()

    def setup_method(self, method):
        self.UserName = id_generator(prefix='TestCreatePolicy')
        super(Test_create_policy, self).setup_method(method)
        try:
            self.user_info = self.a1_r1.eim.CreateUser(UserName=self.UserName)
            self.accesskey_info = self.a1_r1.eim.CreateAccessKey(UserName=self.UserName)
            self.account_sdk = OscSdk(config=OscConfig.get_with_keys(
                az_name=self.a1_r1.config.region.az_name, ak=self.accesskey_info.response.CreateAccessKeyResult.AccessKey.AccessKeyId,
                sk=self.accesskey_info.response.CreateAccessKeyResult.AccessKey.SecretAccessKey))
        except:
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.accesskey_info:
                self.a1_r1.eim.DeleteAccessKey(AccessKeyId=self.accesskey_info.response.CreateAccessKeyResult.AccessKey.AccessKeyId,
                                              UserName=self.UserName)
            if self.user_info:
                self.a1_r1.eim.DeleteUser(UserName=self.UserName)
        finally:
            super(Test_create_policy, self).teardown_method(method)

    def test_T4573_with_ext_fcu_policy(self):
        PolicyName = id_generator(prefix='TestCreatePolicy')
        attach_policy = None
        policy_response = None
        try:
            policy_response = self.a1_r1.eim.CreatePolicy(
                PolicyName=PolicyName, PolicyDocument='{"Statement": [{"Action": ["fcuext:*"], "Resource": ["*"], "Effect": "Allow"}]}')
            attach_policy = self.a1_r1.eim.AttachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            try:
                self.account_sdk.fcu.DescribeInstanceTypes()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'UnauthorizedOperation', None)
            try:
                self.account_sdk.fcu.DescribeDhcpOptions()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'UnauthorizedOperation', None)
            try:
                self.account_sdk.eim.ListAccessKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.lbu.DescribeLoadBalancers()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.icu.ReadCatalog()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'NotImplemented', None)
            try:
                self.account_sdk.kms.ListKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDeniedException', None)
            try:
                self.account_sdk.oapi.ReadVms()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 401, 'AccessDenied', '4', 'User unauthorized to perform this action')
        finally:
            if attach_policy:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            if policy_response:
                self.a1_r1.eim.DeletePolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn)

    def test_T4605_with_direct_link_policy(self):
        PolicyName = id_generator(prefix='TestCreatePolicy')
        policy_response = None
        attach_policy = None
        try:
            policy_response = self.a1_r1.eim.CreatePolicy(
                PolicyName=PolicyName, PolicyDocument='{"Statement": [{"Action": ["directconnect:*"], "Resource": ["*"], "Effect": "Allow"}]}')
            attach_policy = self.a1_r1.eim.AttachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            ret = self.account_sdk.directlink.DescribeLocations()
            assert ret.status_code == 200
            try:
                self.account_sdk.fcu.DescribeDhcpOptions()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'UnauthorizedOperation', None)
            try:
                self.account_sdk.eim.ListAccessKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.lbu.DescribeLoadBalancers()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.icu.ReadCatalog()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'NotImplemented', None)
            try:
                self.account_sdk.kms.ListKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDeniedException', None)
            try:
                self.account_sdk.oapi.ReadVms()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 401, 'AccessDenied', '4', 'User unauthorized to perform this action')
        finally:
            if attach_policy:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            if policy_response:
                self.a1_r1.eim.DeletePolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn)

    def test_T4606_with_lbu_policy(self):
        PolicyName = id_generator(prefix='TestCreatePolicy')
        policy_response = None
        attach_policy = None
        try:
            policy_response = self.a1_r1.eim.CreatePolicy(
                PolicyName=PolicyName, PolicyDocument='{"Statement": [{"Action": ["elasticloadbalancing:*"], "Resource": ["*"], "Effect": "Allow"}]}')
            attach_policy = self.a1_r1.eim.AttachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            ret = self.account_sdk.lbu.DescribeLoadBalancers()
            assert ret.status_code == 200
            try:
                self.account_sdk.fcu.DescribeDhcpOptions()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'UnauthorizedOperation', None)
            try:
                self.account_sdk.eim.ListAccessKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.directlink.DescribeLocations()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDeniedException', None)
            try:
                self.account_sdk.icu.ReadCatalog()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'NotImplemented', None)
            try:
                self.account_sdk.kms.ListKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDeniedException', None)
            try:
                self.account_sdk.oapi.ReadVms()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 401, 'AccessDenied', '4', 'User unauthorized to perform this action')
        finally:
            if attach_policy:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            if policy_response:
                self.a1_r1.eim.DeletePolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn)

    @pytest.mark.region_kms
    def test_T4607_with_kms_policy(self):
        PolicyName = id_generator(prefix='TestCreatePolicy')
        policy_response = None
        attach_policy = None
        try:
            policy_response = self.a1_r1.eim.CreatePolicy(
                PolicyName=PolicyName, PolicyDocument='{"Statement": [{"Action": ["kms:*"], "Resource": ["*"], "Effect": "Allow"}]}')
            attach_policy = self.a1_r1.eim.AttachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            ret = self.account_sdk.kms.ListKeys()
            assert ret.status_code == 200
            try:
                self.account_sdk.fcu.DescribeDhcpOptions()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'UnauthorizedOperation', None)
            try:
                self.account_sdk.eim.ListAccessKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.directlink.DescribeLocations()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDeniedException', None)
            try:
                self.account_sdk.icu.ReadCatalog()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'NotImplemented', None)
            try:
                self.account_sdk.lbu.DescribeLoadBalancers()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.oapi.ReadVms()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 401, 'AccessDenied', '4', 'User unauthorized to perform this action')
        finally:
            if attach_policy:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            if policy_response:
                self.a1_r1.eim.DeletePolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn)
 
    def test_T4608_with_fcu_policy(self):
        PolicyName = id_generator(prefix='TestCreatePolicy')
        attach_policy = None
        policy_response = None
        try:
            policy_response = self.a1_r1.eim.CreatePolicy(
                PolicyName=PolicyName, PolicyDocument='{"Statement": [{"Action": ["fcu:*"], "Resource": ["*"], "Effect": "Allow"}]}')
            attach_policy = self.a1_r1.eim.AttachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            try:
                self.account_sdk.fcu.DescribeInstanceTypes()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'UnauthorizedOperation', None)
            try:
                self.account_sdk.fcu.DescribeDhcpOptions()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'UnauthorizedOperation', None)
            try:
                self.account_sdk.eim.ListAccessKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.lbu.DescribeLoadBalancers()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.icu.ReadCatalog()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'NotImplemented', None)
            try:
                self.account_sdk.kms.ListKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDeniedException', None)
            try:
                self.account_sdk.oapi.ReadVms()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 401, 'AccessDenied', '4', 'User unauthorized to perform this action')
        finally:
            if attach_policy:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            if policy_response:
                self.a1_r1.eim.DeletePolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn)
 
    def test_T4609_with_incorrect_service_policy(self):
        PolicyName = id_generator(prefix='TestCreatePolicy')
        attach_policy = None
        policy_response = None
        try:
            policy_response = self.a1_r1.eim.CreatePolicy(
                PolicyName=PolicyName, PolicyDocument='{"Statement": [{"Action": ["toto:*"], "Resource": ["*"], "Effect": "Allow"}]}')
            attach_policy = self.a1_r1.eim.AttachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            try:
                self.account_sdk.fcu.DescribeDhcpOptions()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'UnauthorizedOperation', None)
            try:
                self.account_sdk.eim.ListAccessKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.lbu.DescribeLoadBalancers()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.icu.ReadCatalog()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'NotImplemented', None)
            try:
                self.account_sdk.kms.ListKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDeniedException', None)
            try:
                self.account_sdk.oapi.ReadVms()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 401, 'AccessDenied', '4', 'User unauthorized to perform this action')
        finally:
            if attach_policy:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            if policy_response:
                self.a1_r1.eim.DeletePolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn)
 
    def test_T4610_with_incorrect_call_policy(self):
        PolicyName = id_generator(prefix='TestCreatePolicy')
        attach_policy = None
        policy_response = None
        try:
            policy_response = self.a1_r1.eim.CreatePolicy(
                PolicyName=PolicyName, PolicyDocument='{"Statement": [{"Action": ["ec2:toto"], "Resource": ["*"], "Effect": "Allow"}]}')
            attach_policy = self.a1_r1.eim.AttachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            try:
                self.account_sdk.fcu.DescribeDhcpOptions()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'UnauthorizedOperation', None)
            try:
                self.account_sdk.eim.ListAccessKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.lbu.DescribeLoadBalancers()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.icu.ReadCatalog()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'NotImplemented', None)
            try:
                self.account_sdk.kms.ListKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDeniedException', None)
            try:
                self.account_sdk.oapi.ReadVms()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 401, 'AccessDenied', '4', 'User unauthorized to perform this action')
        finally:
            if attach_policy:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            if policy_response:
                self.a1_r1.eim.DeletePolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn)
 
    def test_T4614_with_ext_fcu_call(self):
        PolicyName = id_generator(prefix='TestCreatePolicy')
        attach_policy = None
        policy_response = None
        try:
            policy_response = self.a1_r1.eim.CreatePolicy(
                PolicyName=PolicyName,
                PolicyDocument='{"Statement": [{"Action": ["ec2:DescribeInstanceTypes"], "Resource": ["*"], "Effect": "Allow"}]}')
            attach_policy = self.a1_r1.eim.AttachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            ret = self.account_sdk.fcu.DescribeInstanceTypes()
            assert ret.status_code == 200
            try:
                self.account_sdk.fcu.DescribeDhcpOptions()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'UnauthorizedOperation', None)
            try:
                self.account_sdk.eim.ListAccessKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.lbu.DescribeLoadBalancers()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.icu.ReadCatalog()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'NotImplemented', None)
            try:
                self.account_sdk.kms.ListKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDeniedException', None)
            try:
                self.account_sdk.oapi.ReadVms()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 401, 'AccessDenied', '4', 'User unauthorized to perform this action')
        finally:
            if attach_policy:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            if policy_response:
                self.a1_r1.eim.DeletePolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn)
 
    def test_T4615_with_fcu_call(self):
        PolicyName = id_generator(prefix='TestCreatePolicy')
        attach_policy = None
        policy_response = None
        try:
            policy_response = self.a1_r1.eim.CreatePolicy(
                PolicyName=PolicyName,
                PolicyDocument='{"Statement": [{"Action": ["ec2:DescribeDhcpOptions"], "Resource": ["*"], "Effect": "Allow"}]}')
            attach_policy = self.a1_r1.eim.AttachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            self.account_sdk.fcu.DescribeDhcpOptions()
            try:
                self.account_sdk.fcu.DescribeInstanceTypes()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'UnauthorizedOperation', None)
            try:
                self.account_sdk.eim.ListAccessKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.lbu.DescribeLoadBalancers()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDenied', None)
            try:
                self.account_sdk.icu.ReadCatalog()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'NotImplemented', None)
            try:
                self.account_sdk.kms.ListKeys()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'AccessDeniedException', None)
            try:
                self.account_sdk.oapi.ReadVms()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 401, 'AccessDenied', '4', 'User unauthorized to perform this action')
        finally:
            if attach_policy:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            if policy_response:
                self.a1_r1.eim.DeletePolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn)


    def test_T4811_with_oapi_policy(self):
        PolicyName = id_generator(prefix='TestCreatePolicy')
        attach_policy = None
        policy_response = None
        try:
            policy_response = self.a1_r1.eim.CreatePolicy(
                PolicyName=PolicyName,
                PolicyDocument='{"Statement": [{"Action": ["api:*"], "Resource": ["*"], "Effect": "Allow"}]}')
            attach_policy = self.a1_r1.eim.AttachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            self.account_sdk.oapi.ReadVms()
            try:
                self.account_sdk.fcu.DescribeDhcpOptions()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'UnauthorizedOperation', None)
            try:
                self.account_sdk.fcu.DescribeInstanceTypes()
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'UnauthorizedOperation', None)
        finally:
            if attach_policy:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=self.UserName)
            if policy_response:
                self.a1_r1.eim.DeletePolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn)
