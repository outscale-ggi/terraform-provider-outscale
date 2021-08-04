
import re
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
import qa_sdk_pub.osc_api as osc_api
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools import misc
from qa_test_tools.config import OscConfig
from qa_tina_tools.test_base import OscTinaTest


class Test_DirectLink(OscTinaTest):

    @pytest.mark.tag_sec_traceability
    def test_T3844_check_request_id(self):
        ret = self.a1_r1.directlink.DescribeLocations()
        assert re.search("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", ret.response.requestId)

    def test_T3845_invalid_call(self):
        try:
            self.a1_r1.directlink.foo()
            assert False, 'Call not should have been successful'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == "UnknownOperationException"
            assert hasattr(error, 'message')

    def test_T3846_invalid_param(self):
        try:
            self.a1_r1.directlink.DescribeLocations(foo='bar')
            assert False, 'Call not should have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, "DirectConnectClientException", "Operation doesn't expect any parameters")

    def test_T3847_method_get(self):
        try:
            self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_METHOD: 'GET'})
            assert False, 'Call not should have been successful'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == "SerializationException"
            assert hasattr(error, 'message')

    # def test_T3848_check_log(self):
    #    # TODO add test to check log
    #    known_error('PQA-253', 'Add tool to check API logs.')

    @pytest.mark.tag_sec_confidentiality
    def test_T3849_without_authentication(self):
        try:
            self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty})
            assert False, 'Call not should have been successful'
        except OscApiException as error:
            misc.assert_error(error, 401,"AuthFailure",
                              "Outscale was not able to validate the provided access credentials. Invalid login/password or password has expired.")

    @pytest.mark.tag_sec_confidentiality
    def test_T3850_invalid_authentication(self):
        sk_bkp = self.a1_r1.config.account.sk
        self.a1_r1.config.account.sk = "foo"
        try:
            self.a1_r1.directlink.DescribeLocations()
            assert False, 'Call not should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 403, "SignatureDoesNotMatch",
                              "The request signature we calculated does not match the signature you provided. " + \
                                    "Check your AWS Secret Access Key and signing method. Consult the service documentation for details.")
        finally:
            self.a1_r1.config.account.sk = sk_bkp

    @pytest.mark.tag_sec_availability
    def test_T3851_throttling(self):
        osc_api.disable_throttling()
        nb_ok = 0
        nb_ko = 0
        for _ in range(10):
            try:
                self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                nb_ok += 1
            except OscApiException as error:
                if error.status_code == 503:
                    nb_ko += 1
                else:
                    raise
        osc_api.enable_throttling()
        assert nb_ok != 0
        assert nb_ko != 0

    def test_T4577_with_eim_user(self):
        user_name = misc.id_generator(prefix='T4577')
        policy_name = misc.id_generator(prefix='T4577')
        account_sdk = None
        attach_policy = None
        user_info = None
        policy_response = None
        accesskey_info = None
        try:
            user_info = self.a1_r1.eim.CreateUser(UserName=user_name)
            policy_response = self.a1_r1.eim.CreatePolicy(
                PolicyName=policy_name,
                PolicyDocument='{"Statement": [{"Action": ["directconnect:*"], "Resource": ["*"], "Effect": "Allow"}]}')
            attach_policy = self.a1_r1.eim.AttachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=user_name)
            accesskey_info = self.a1_r1.eim.CreateAccessKey(UserName=user_name)
            account_sdk = OscSdk(config=OscConfig.get_with_keys(
                az_name=self.a1_r1.config.region.az_name, ak=accesskey_info.response.CreateAccessKeyResult.AccessKey.AccessKeyId,
                sk=accesskey_info.response.CreateAccessKeyResult.AccessKey.SecretAccessKey))
            ret = account_sdk.directlink.DescribeLocations()
            assert ret.status_code == 200
            try:
                account_sdk.fcu.DescribeDhcpOptions()
            except OscApiException as error:
                misc.assert_error(error, 400, 'UnauthorizedOperation', None)
            try:
                account_sdk.eim.ListAccessKeys()
            except OscApiException as error:
                misc.assert_error(error, 400, 'AccessDenied', None)
            try:
                account_sdk.lbu.DescribeLoadBalancers()
            except OscApiException as error:
                misc.assert_error(error, 400, 'AccessDenied', None)
            try:
                account_sdk.icu.ReadCatalog()
            except OscApiException as error:
                misc.assert_error(error, 400, 'NotImplemented', None)
            try:
                account_sdk.oapi.ReadVms()
            except OscApiException as error:
                misc.assert_error(error, 401, '4', 'AccessDenied')
        finally:
            if attach_policy:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=user_name)
            if policy_response:
                self.a1_r1.eim.DeletePolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn)
            if accesskey_info:
                self.a1_r1.eim.DeleteAccessKey(AccessKeyId=accesskey_info.response.CreateAccessKeyResult.AccessKey.AccessKeyId, UserName=user_name)
            if user_info:
                self.a1_r1.eim.DeleteUser(UserName=user_name)
